use mysql_async::Row;
use serde::Serialize;
use std::fmt::Write;

pub const RECORD_SQL: &str = r#"
    SELECT
        newrecord.achievements, newrecord.fc, newrecord.fs, newrecord.dxScore,
        chart.ds AS ds, chart.level AS level, chart.difficulty AS diff,
        music.type AS `type`, music.id AS id, music.is_new AS is_new,
        music.title AS title, music.artist AS artist, music.genre AS genre,
        music.bpm AS bpm, music.version AS version,
        music.release_date AS release_date, chart.charter AS charter
    FROM newrecord
    JOIN chart ON newrecord.chart_id = chart.id
    JOIN music ON chart.music_id = music.id
    WHERE newrecord.player_id = ?
"#;
const COEFFICIENTS: &[(f64, f64, &str)] = &[
    (0., 0., "d"),
    (10., 1.6, "d"),
    (20., 3.2, "d"),
    (30., 4.8, "d"),
    (40., 6.4, "d"),
    (50., 8., "c"),
    (60., 9.6, "b"),
    (70., 11.2, "bb"),
    (75., 12., "bbb"),
    (79.9999, 12.8, "bbb"),
    (80., 13.6, "a"),
    (90., 15.2, "aa"),
    (94., 16.8, "aaa"),
    (96.9999, 17.6, "aaa"),
    (97., 20., "s"),
    (98., 20.3, "sp"),
    (98.9999, 20.6, "sp"),
    (99., 20.8, "ss"),
    (99.5, 21.1, "ssp"),
    (99.9999, 21.4, "ssp"),
    (100., 21.6, "sss"),
    (100.4999, 22.2, "sss"),
    (100.5, 22.4, "sssp"),
];

#[derive(Clone, Serialize)]
pub struct Record {
    pub title: String,
    pub level: String,
    pub level_index: i64,
    pub level_label: &'static str,
    #[serde(rename = "type")]
    pub kind: String,
    #[serde(rename = "dxScore")]
    pub dx_score: i64,
    pub achievements: f64,
    pub rate: &'static str,
    pub fc: String,
    pub fs: String,
    pub ra: i64,
    pub ds: f64,
    pub song_id: i64,
    #[serde(skip)]
    pub is_new: bool,
    #[serde(skip)]
    pub artist: String,
    #[serde(skip)]
    pub genre: String,
    #[serde(skip)]
    pub bpm: f64,
    #[serde(skip)]
    pub version: String,
    #[serde(skip)]
    pub release_date: String,
    #[serde(skip)]
    pub charter: String,
    #[serde(skip)]
    pub raw_ra: i64,
}

#[derive(Clone, Serialize)]
pub struct Payload {
    pub username: String,
    pub rating: i64,
    pub additional_rating: Option<i64>,
    pub nickname: Option<String>,
    pub plate: Option<String>,
    pub records: Vec<Record>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub filters: Option<std::collections::BTreeMap<String, Vec<String>>>,
}

pub fn score(achievement: f64, ds: f64) -> (i64, &'static str) {
    let &(_, coefficient, rate) = COEFFICIENTS
        .iter()
        .rev()
        .find(|&&(threshold, _, _)| achievement >= threshold)
        .unwrap_or(&COEFFICIENTS[0]);
    (
        (coefficient * ds * achievement.min(100.5) / 100.) as i64,
        rate,
    )
}

pub fn value<T: mysql_async::prelude::FromValue>(row: &Row, key: &str) -> Result<T, String> {
    row.get_opt(key)
        .ok_or_else(|| format!("missing column {key}"))?
        .map_err(|_| {
            eprintln!("Unexpected SQL type for column {key}");
            format!("invalid column type {key}")
        })
}

pub fn decode(row: Row) -> Result<Record, String> {
    let achievements = value(&row, "achievements")?;
    let ds = value(&row, "ds")?;
    let song_id: i64 = value(&row, "id")?;
    let level_index: i64 = value(&row, "level")?;
    let (mut ra, rate) = score(achievements, ds);
    let level_label = if song_id >= 100000 {
        ra = 0;
        "Utage"
    } else {
        *["Basic", "Advanced", "Expert", "Master", "Re:MASTER"]
            .get(level_index as usize)
            .ok_or("invalid chart level")?
    };
    Ok(Record {
        title: value(&row, "title")?,
        level: value(&row, "diff")?,
        level_index,
        level_label,
        kind: value(&row, "type")?,
        dx_score: value(&row, "dxScore")?,
        achievements,
        rate,
        fc: value(&row, "fc")?,
        fs: value(&row, "fs")?,
        ra,
        ds,
        song_id,
        is_new: value(&row, "is_new")?,
        artist: value(&row, "artist")?,
        genre: value(&row, "genre")?,
        bpm: value::<i64>(&row, "bpm")? as f64,
        version: value(&row, "version")?,
        release_date: value(&row, "release_date")?,
        charter: value(&row, "charter")?,
        raw_ra: score(achievements, ds).0,
    })
}

pub fn rating(records: &[Record]) -> (i64, i64, usize, usize) {
    let mut old: Vec<&Record> = records
        .iter()
        .filter(|r| r.song_id < 100000 && !r.is_new)
        .collect();
    let mut new: Vec<&Record> = records
        .iter()
        .filter(|r| r.song_id < 100000 && r.is_new)
        .collect();
    for group in [&mut old, &mut new] {
        group.sort_by(|a, b| {
            b.ra.cmp(&a.ra)
                .then_with(|| b.ds.total_cmp(&a.ds))
                .then_with(|| b.achievements.total_cmp(&a.achievements))
        });
    }
    old.truncate(35);
    new.truncate(15);
    let new_ra: i64 = new.iter().map(|r| r.ra).sum();
    (
        new_ra + old.iter().map(|r| r.ra).sum::<i64>(),
        new_ra,
        old.len(),
        new.len(),
    )
}
// Match Quart's default ensure_ascii=True so smaller UTF-8 output cannot bias the benchmark.
pub fn serialize<T: Serialize>(payload: &T) -> Result<String, serde_json::Error> {
    let json = serde_json::to_string(payload)?;
    let mut ascii = String::with_capacity(json.len());
    for ch in json.chars() {
        if ch.is_ascii() {
            ascii.push(ch);
        } else {
            for unit in ch.encode_utf16(&mut [0; 2]) {
                write!(&mut ascii, "\\u{unit:04x}").unwrap();
            }
        }
    }
    ascii.push('\n');
    Ok(ascii)
}

pub fn best(records: &[Record], b50: bool) -> (Vec<Record>, Vec<Record>) {
    let mut old: Vec<Record> = records
        .iter()
        .filter(|r| !r.is_new && (!b50 || r.song_id < 100000))
        .cloned()
        .collect();
    let mut new: Vec<Record> = records
        .iter()
        .filter(|r| r.is_new && (!b50 || r.song_id < 100000))
        .cloned()
        .collect();
    for group in [&mut old, &mut new] {
        group.sort_by(|a, b| {
            b.raw_ra
                .cmp(&a.raw_ra)
                .then_with(|| b.ds.total_cmp(&a.ds))
                .then_with(|| b.achievements.total_cmp(&a.achievements))
        });
    }
    old.truncate(if b50 { 35 } else { 25 });
    new.truncate(15);
    (old, new)
}

pub fn mask(record: &mut Record) {
    record.dx_score = 0;
    let &(minimum, coefficient, _) = COEFFICIENTS
        .iter()
        .rev()
        .find(|&&(t, _, _)| record.achievements >= t)
        .unwrap_or(&COEFFICIENTS[0]);
    record.achievements = if record.achievements >= 100.5 {
        if record.fc == "ap" || record.fc == "app" {
            101.
        } else {
            (record.achievements * 10.).floor() / 10.
        }
    } else if coefficient == 0. {
        0.
    } else {
        let value = record.raw_ra as f64 * 100. / coefficient / record.ds;
        if value < minimum {
            minimum
        } else {
            (value * 1000.).ceil() / 1000.
        }
    };
}
