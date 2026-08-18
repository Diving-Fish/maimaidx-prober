"""服务端成绩过滤。

/player/records 与 /chuni/player/records 共用这一套：调用方把条件写在查询串里，
服务端只回符合条件的成绩，省掉「拉全量再在客户端筛」的来回。

约定：

- **多值**：重复参数（`?fc=fc&fc=ap`）或逗号分隔（`?fc=fc,ap`），两者等价，取并集。
  值本身含逗号时（曲名、曲师、谱师）请用重复参数形式。
- **数值**：`13.5` 严格相等；`13..14` 闭区间；`13..` 只有下界；`..14` 只有上界。
  一个参数里可以混用，如 `ds=13..13.9,14.5`。
- **字符串**：完全匹配，忽略大小写。`?fc=` 匹配空值（即非 FC 的成绩）。
- **布尔**：`1/0/true/false/yes/no`。
- 认不出的查询参数一律忽略——老客户端可能带缓存参数，为它们返回 400 属于误伤。
  但认得的字段值解析失败会返回 400：静默放行会让调用方以为筛过了，
  拿到全量数据还以为是过滤结果，比报错糟得多。

过滤跑在 record_json 的输出上而不是原始行上，这一点是刻意的：开了 mask 的用户
其 achievements 已经被模糊过，如果按真实值过滤再回模糊值，调用方可以拿区间参数
二分出真实成绩——那 mask 就白设了。能筛的只能是能看见的。
"""
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

NUM = 'num'
STR = 'str'
BOOL = 'bool'

_EPS = 1e-9
_TRUE = ('1', 'true', 'yes', 'y', 'on')
_FALSE = ('0', 'false', 'no', 'n', 'off')


class FilterError(Exception):
    """查询参数写错了，应当以 400 回给调用方。"""


def _to_num(field: str, tok: str) -> float:
    try:
        return float(tok)
    except ValueError:
        raise FilterError(f'参数 {field} 的值 "{tok}" 不是数字')


def _num_predicate(field: str, tokens: List[str]) -> Callable[[Any], bool]:
    clauses: List[Tuple[Optional[float], Optional[float]]] = []
    exacts: List[float] = []
    for tok in tokens:
        if '..' in tok:
            lo_s, _, hi_s = tok.partition('..')
            lo_s, hi_s = lo_s.strip(), hi_s.strip()
            if lo_s == '' and hi_s == '':
                raise FilterError(f'参数 {field} 的区间 "{tok}" 至少要有一个端点')
            lo = _to_num(field, lo_s) if lo_s else None
            hi = _to_num(field, hi_s) if hi_s else None
            if lo is not None and hi is not None and lo > hi:
                raise FilterError(f'参数 {field} 的区间 "{tok}" 下界大于上界')
            clauses.append((lo, hi))
        else:
            exacts.append(_to_num(field, tok))

    def pred(value: Any) -> bool:
        if value is None or isinstance(value, bool):
            return False
        try:
            v = float(value)
        except (TypeError, ValueError):
            return False
        for e in exacts:
            if abs(v - e) <= _EPS:
                return True
        for lo, hi in clauses:
            if (lo is None or v >= lo - _EPS) and (hi is None or v <= hi + _EPS):
                return True
        return False

    return pred


def _str_predicate(field: str, tokens: List[str]) -> Callable[[Any], bool]:
    wanted = {t.lower() for t in tokens}

    def pred(value: Any) -> bool:
        if value is None:
            value = ''
        return str(value).lower() in wanted

    return pred


def _bool_predicate(field: str, tokens: List[str]) -> Callable[[Any], bool]:
    wanted = set()
    for tok in tokens:
        low = tok.strip().lower()
        if low in _TRUE:
            wanted.add(True)
        elif low in _FALSE:
            wanted.add(False)
        else:
            raise FilterError(f'参数 {field} 的值 "{tok}" 不是布尔值')

    def pred(value: Any) -> bool:
        return bool(value) in wanted

    return pred


_BUILDERS = {NUM: _num_predicate, STR: _str_predicate, BOOL: _bool_predicate}


def raw_values(args, name: str) -> List[str]:
    """取一个参数的全部值：重复参数与逗号分隔等价。

    字符串字段允许空值（`?fc=` 表示筛非 FC 的成绩），所以这里不丢弃空串；
    但整个参数没出现时返回空列表，调用方据此判断「没有这个条件」。
    """
    out: List[str] = []
    for v in args.getlist(name):
        out.extend(part.strip() for part in v.split(','))
    return out


def build(args, spec: Dict[str, str],
          aliases: Optional[Dict[str, str]] = None
          ) -> Tuple[List[Tuple[str, Callable[[Any], bool]]], Dict[str, List[str]]]:
    """按 spec 从查询串里解析出过滤条件。

    返回 (matchers, echo)：matchers 是 (字段, 判定函数) 列表，字段间取交集；
    echo 是实际生效的条件，回给调用方自查，免得参数名写错了还以为筛过。
    """
    aliases = aliases or {}
    collected: Dict[str, List[str]] = {}
    for name, canonical in list(aliases.items()) + [(f, f) for f in spec]:
        vals = raw_values(args, name)
        if vals:
            collected.setdefault(canonical, []).extend(vals)

    matchers = []
    echo = {}
    for field, tokens in collected.items():
        matchers.append((field, _BUILDERS[spec[field]](field, tokens)))
        echo[field] = tokens
    return matchers, echo


def str_matcher(field: str, values: List[str]) -> Tuple[str, Callable[[Any], bool]]:
    """手工造一条字符串条件。给 plate 这类需要先翻译再匹配的参数用。"""
    return field, _str_predicate(field, values)


def match(view: Dict[str, Any],
          matchers: Iterable[Tuple[str, Callable[[Any], bool]]]) -> bool:
    """一条成绩是否满足全部条件。字段间取交集，同字段多值取并集。"""
    for field, pred in matchers:
        if not pred(view.get(field)):
            return False
    return True
