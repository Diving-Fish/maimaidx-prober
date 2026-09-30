use crate::filters::Filters;
use crate::records::{self, Record};

fn sample_record() -> Record {
    let (rating, rate) = records::score(99.9999, 14.5);
    Record {
        title: "Test, Song".into(),
        level: "14".into(),
        level_index: 3,
        level_label: "Master",
        kind: "DX".into(),
        dx_score: 2000,
        achievements: 99.9999,
        rate,
        fc: "ap".into(),
        fs: "".into(),
        ra: rating,
        ds: 14.5,
        song_id: 1,
        is_new: false,
        artist: "Artist".into(),
        genre: "GAME".into(),
        bpm: 180.,
        version: "maimai PLUS".into(),
        release_date: "20200101".into(),
        charter: "Charter".into(),
        raw_ra: rating,
    }
}

#[test]
fn score_boundaries_match_python() {
    let cases: Vec<(f64, f64, i64, String)> =
        serde_json::from_str(include_str!("../tests/score_cases.json")).unwrap();
    for (achievement, constant, expected_rating, expected_rate) in cases {
        let (rating, rate) = records::score(achievement, constant);
        assert_eq!((rating, rate), (expected_rating, expected_rate.as_str()));
    }
}

#[test]
fn best_lists_keep_original_records_and_exclude_utage_only_for_b50() {
    let mut records = vec![sample_record(); 100];
    for (index, record) in records.iter_mut().enumerate() {
        record.song_id = index as i64;
        record.is_new = index >= 50;
    }
    records[0].song_id = 100000;
    records[0].raw_ra = 999;
    records[0].ra = 0;
    let (old, new) = records::best(&records, false);
    assert_eq!((old.len(), new.len()), (25, 15));
    assert_eq!(old[0].song_id, 100000);
    let (old, new) = records::best(&records, true);
    assert_eq!((old.len(), new.len()), (35, 15));
    assert!(old.iter().all(|record| record.song_id < 100000));
    assert_eq!(records.len(), 100);
}

#[test]
fn masking_happens_before_filtering() {
    let mut record = sample_record();
    record.achievements = 97.1234;
    (record.raw_ra, record.rate) = records::score(record.achievements, record.ds);
    record.ra = record.raw_ra;
    let original = record.achievements;
    records::mask(&mut record);
    assert_eq!(record.dx_score, 0);
    assert_ne!(record.achievements, original);
    assert!(
        !Filters::build("achievements=97.1234")
            .unwrap()
            .matches(&record)
    );
    record.achievements = 100.5;
    records::mask(&mut record);
    assert_eq!(record.achievements, 101.);
}

#[test]
fn filter_aliases_ranges_and_intersection() {
    let record = sample_record();
    assert!(
        Filters::build("music_id=1&ds=14..15&fc=ap,app&is_new=false")
            .unwrap()
            .matches(&record)
    );
    assert!(
        !Filters::build("music_id=2&ds=14..15")
            .unwrap()
            .matches(&record)
    );
    assert!(
        Filters::build("plate=真将&version=maimai%20PLUS")
            .unwrap()
            .matches(&record)
    );
    assert!(
        !Filters::build("plate=真将&version=maimai")
            .unwrap()
            .matches(&record)
    );
    assert!(Filters::build("unknown=ignored").unwrap().echo.is_empty());
    assert_eq!(
        Filters::build("music_id=1&id=2&song_id=3").unwrap().echo["song_id"],
        ["2", "1", "3"]
    );
}

#[test]
fn invalid_filters_are_rejected() {
    for query in [
        "ds=..",
        "ds=15..10",
        "ds=bad",
        "ds=1__0",
        "is_new=maybe",
        "plate=不存在",
    ] {
        assert!(Filters::build(query).is_err(), "{query}");
    }
}

#[test]
fn unicode_serialization_roundtrips() {
    let json = serde_json::json!({"nickname": "水鱼😀"});
    let output = records::serialize(&json).unwrap();
    assert!(output.is_ascii());
    assert_eq!(
        serde_json::from_str::<serde_json::Value>(&output).unwrap(),
        json
    );
}
