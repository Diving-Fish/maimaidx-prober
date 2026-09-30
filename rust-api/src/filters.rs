use std::collections::{BTreeMap, HashMap};
use std::sync::LazyLock;

use crate::ApiError;
use crate::records::Record;

const EPSILON: f64 = 1e-9;
const NUMBER_FIELDS: &[&str] = &[
    "song_id",
    "level_index",
    "ds",
    "bpm",
    "achievements",
    "dxScore",
    "ra",
];
const STRING_FIELDS: &[&str] = &[
    "title",
    "artist",
    "genre",
    "charter",
    "version",
    "release_date",
    "type",
    "level",
    "level_label",
    "rate",
    "fc",
    "fs",
];
const FIELD_ALIASES: &[(&str, &str)] = &[
    ("id", "song_id"),
    ("music_id", "song_id"),
    ("dx_score", "dxScore"),
    ("difficulty", "level_index"),
];
static PLATE_VERSIONS: LazyLock<HashMap<String, Vec<String>>> = LazyLock::new(|| {
    serde_json::from_str(include_str!("plate_versions.json"))
        .expect("the checked-in plate mapping must be valid JSON")
});

type QueryPairs = Vec<(String, String)>;

#[derive(Debug)]
enum NumberCondition {
    Exact(f64),
    Range {
        lower: Option<f64>,
        upper: Option<f64>,
    },
}

impl NumberCondition {
    fn matches(&self, value: f64) -> bool {
        match self {
            Self::Exact(expected) => (value - expected).abs() <= EPSILON,
            Self::Range { lower, upper } => {
                lower.is_none_or(|bound| value >= bound - EPSILON)
                    && upper.is_none_or(|bound| value <= bound + EPSILON)
            }
        }
    }
}

#[derive(Debug)]
enum Condition {
    Numbers(Vec<NumberCondition>),
    Strings(Vec<String>),
    Booleans(Vec<bool>),
}

#[derive(Debug)]
struct Matcher {
    field: String,
    condition: Condition,
}

impl Matcher {
    fn matches(&self, record: &Record) -> bool {
        match &self.condition {
            Condition::Booleans(allowed) => allowed.contains(&record.is_new),
            Condition::Numbers(conditions) => {
                let value = match self.field.as_str() {
                    "song_id" => record.song_id as f64,
                    "level_index" => record.level_index as f64,
                    "ds" => record.ds,
                    "bpm" => record.bpm,
                    "achievements" => record.achievements,
                    "dxScore" => record.dx_score as f64,
                    "ra" => record.ra as f64,
                    _ => return false,
                };
                conditions.iter().any(|condition| condition.matches(value))
            }
            Condition::Strings(allowed) => {
                let value = match self.field.as_str() {
                    "title" => &record.title,
                    "artist" => &record.artist,
                    "genre" => &record.genre,
                    "charter" => &record.charter,
                    "version" => &record.version,
                    "release_date" => &record.release_date,
                    "type" => &record.kind,
                    "level" => &record.level,
                    "level_label" => record.level_label,
                    "rate" => record.rate,
                    "fc" => &record.fc,
                    "fs" => &record.fs,
                    _ => return false,
                };
                allowed.contains(&value.to_lowercase())
            }
        }
    }
}

#[derive(Debug)]
pub struct Filters {
    matchers: Vec<Matcher>,
    pub echo: BTreeMap<String, Vec<String>>,
}

impl Filters {
    pub fn build(query: &str) -> Result<Self, ApiError> {
        let pairs = query_pairs(query);
        let collected = collect_filter_values(&pairs);
        let mut filters = Self {
            matchers: Vec::new(),
            echo: BTreeMap::new(),
        };

        for (field, tokens) in collected {
            let condition = parse_condition(&field, &tokens)?;
            filters.echo.insert(field.clone(), tokens);
            filters.matchers.push(Matcher { field, condition });
        }

        let plates = raw_values(&pairs, "plate");
        if !plates.is_empty() {
            // Keep plate and explicit version as separate matchers: they intersect.
            filters.matchers.push(Matcher {
                field: "version".into(),
                condition: Condition::Strings(versions_for_plates(&plates)?),
            });
            filters.echo.insert("plate".into(), plates);
        }
        Ok(filters)
    }

    pub fn matches(&self, record: &Record) -> bool {
        self.matchers.iter().all(|matcher| matcher.matches(record))
    }
}

pub fn query_pairs(query: &str) -> QueryPairs {
    url::form_urlencoded::parse(query.as_bytes())
        .into_owned()
        .collect()
}

fn raw_values(pairs: &QueryPairs, name: &str) -> Vec<String> {
    pairs
        .iter()
        .filter(|(key, _)| key == name)
        .flat_map(|(_, value)| value.split(',').map(|part| part.trim().to_owned()))
        .collect()
}

fn collect_filter_values(pairs: &QueryPairs) -> BTreeMap<String, Vec<String>> {
    let names = FIELD_ALIASES.iter().copied().chain(
        NUMBER_FIELDS
            .iter()
            .chain(STRING_FIELDS)
            .chain([&"is_new"])
            .map(|&name| (name, name)),
    );
    let mut collected = BTreeMap::<String, Vec<String>>::new();
    for (name, canonical) in names {
        let values = raw_values(pairs, name);
        if !values.is_empty() {
            collected
                .entry(canonical.into())
                .or_default()
                .extend(values);
        }
    }
    collected
}

fn parse_condition(field: &str, tokens: &[String]) -> Result<Condition, ApiError> {
    if NUMBER_FIELDS.contains(&field) {
        let conditions = tokens
            .iter()
            .map(|token| parse_number_condition(field, token))
            .collect::<Result<_, _>>()?;
        return Ok(Condition::Numbers(conditions));
    }
    if field == "is_new" {
        let values = tokens
            .iter()
            .map(|token| match token.to_lowercase().as_str() {
                "1" | "true" | "yes" | "y" | "on" => Ok(true),
                "0" | "false" | "no" | "n" | "off" => Ok(false),
                _ => Err(ApiError::message(
                    400,
                    &format!("参数 {field} 的值 \"{token}\" 不是布尔值"),
                )),
            })
            .collect::<Result<_, _>>()?;
        return Ok(Condition::Booleans(values));
    }
    Ok(Condition::Strings(
        tokens.iter().map(|token| token.to_lowercase()).collect(),
    ))
}

fn parse_number(field: &str, token: &str) -> Result<f64, ApiError> {
    let error = || ApiError::message(400, &format!("参数 {field} 的值 \"{token}\" 不是数字"));
    // Python float() permits underscores only between decimal digits.
    let bytes = token.as_bytes();
    for (index, &byte) in bytes.iter().enumerate() {
        if byte == b'_'
            && (index == 0
                || index + 1 == bytes.len()
                || !bytes[index - 1].is_ascii_digit()
                || !bytes[index + 1].is_ascii_digit())
        {
            return Err(error());
        }
    }
    token.replace('_', "").parse().map_err(|_| error())
}

fn parse_number_condition(field: &str, token: &str) -> Result<NumberCondition, ApiError> {
    let Some((lower, upper)) = token.split_once("..") else {
        return Ok(NumberCondition::Exact(parse_number(field, token)?));
    };
    let (lower, upper) = (lower.trim(), upper.trim());
    if lower.is_empty() && upper.is_empty() {
        return Err(ApiError::message(
            400,
            &format!("参数 {field} 的区间 \"{token}\" 至少要有一个端点"),
        ));
    }
    let lower = if lower.is_empty() {
        None
    } else {
        Some(parse_number(field, lower)?)
    };
    let upper = if upper.is_empty() {
        None
    } else {
        Some(parse_number(field, upper)?)
    };
    if lower.zip(upper).is_some_and(|(lower, upper)| lower > upper) {
        return Err(ApiError::message(
            400,
            &format!("参数 {field} 的区间 \"{token}\" 下界大于上界"),
        ));
    }
    Ok(NumberCondition::Range { lower, upper })
}

fn versions_for_plates(plates: &[String]) -> Result<Vec<String>, ApiError> {
    let mut versions = Vec::new();
    for plate in plates {
        let mapping = PLATE_VERSIONS
            .get(plate)
            .or_else(|| {
                ["霸者", "舞舞", "極", "将", "神"]
                    .iter()
                    .find_map(|suffix| {
                        plate
                            .strip_suffix(suffix)
                            .and_then(|prefix| PLATE_VERSIONS.get(prefix))
                    })
            })
            .ok_or_else(|| {
                ApiError::message(400, &format!("参数 plate 的值 \"{plate}\" 不是已知的牌子"))
            })?;
        versions.extend(mapping.iter().map(|version| version.to_lowercase()));
    }
    Ok(versions)
}
