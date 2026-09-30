use crate::records::{RECORD_SQL, Record, decode, value};
use crate::{ApiError, AppState};
use mysql_async::{Row, Value, prelude::Queryable};

const PLAYER_COLUMNS: &str = "
    id, username, rating, maimai_new_rating, maimai_legacy_count,
    maimai_new_count, additional_rating, nickname, plate, privacy,
    mask, accept_agreement, user_general_data, access_time
";
const ACCESS_TIME_WRITE_INTERVAL_SECONDS: i64 = 300;

#[derive(Clone, Debug)]
pub struct Player {
    pub id: i64,
    pub username: String,
    pub rating: i64,
    pub new_rating: i64,
    pub old_count: Option<i64>,
    pub new_count: Option<i64>,
    pub additional_rating: Option<i64>,
    pub nickname: Option<String>,
    pub plate: Option<String>,
    pub privacy: bool,
    pub mask: bool,
    pub accept_agreement: bool,
    pub general_data: Option<String>,
    pub access_time: i64,
}

impl Player {
    fn from_row(row: Row) -> Result<Self, ApiError> {
        Ok(Self {
            id: value(&row, "id")?,
            username: value(&row, "username")?,
            rating: value(&row, "rating")?,
            new_rating: value(&row, "maimai_new_rating")?,
            old_count: value(&row, "maimai_legacy_count")?,
            new_count: value(&row, "maimai_new_count")?,
            additional_rating: value(&row, "additional_rating")?,
            nickname: value(&row, "nickname")?,
            plate: value(&row, "plate")?,
            privacy: value::<Option<bool>>(&row, "privacy")?.unwrap_or(false),
            mask: value::<Option<bool>>(&row, "mask")?.unwrap_or(false),
            accept_agreement: value::<Option<bool>>(&row, "accept_agreement")?.unwrap_or(false),
            general_data: value(&row, "user_general_data")?,
            access_time: value::<Option<i64>>(&row, "access_time")?.unwrap_or(0),
        })
    }
}

#[derive(Clone, Copy)]
pub enum Lookup {
    Id,
    Username,
    ImportToken,
    Qq,
    Channel,
}

impl Lookup {
    fn column(self) -> &'static str {
        match self {
            Self::Id => "id",
            Self::Username => "username",
            Self::ImportToken => "import_token",
            Self::Qq => "bind_qq",
            Self::Channel => "qq_channel_uid",
        }
    }
}

pub async fn find(state: &AppState, field: Lookup, key: &str) -> Result<Option<Player>, ApiError> {
    let mut connection = state.pool.get_conn().await?;
    let row: Option<Row> = connection
        .exec_first(
            format!(
                "SELECT {PLAYER_COLUMNS} FROM player WHERE {}=? LIMIT 1",
                field.column()
            ),
            (key,),
        )
        .await?;
    row.map(Player::from_row).transpose()
}

pub async fn by_qq(state: &AppState, key: &str) -> Result<Option<Player>, ApiError> {
    if let Some(player) = find(state, Lookup::Qq, key).await? {
        return Ok(Some(player));
    }
    find(state, Lookup::Channel, key).await
}

pub async fn records(state: &AppState, player: &Player) -> Result<Vec<Record>, ApiError> {
    let mut connection = state.pool.get_conn().await?;
    let rows: Vec<Row> = connection
        .query(RECORD_SQL.replacen('?', &player.id.to_string(), 1))
        .await?;
    rows.into_iter()
        .map(|row| decode(row).map_err(ApiError::from))
        .collect()
}

pub async fn update_rating(
    state: &AppState,
    player: &mut Player,
    total_rating: i64,
    new_rating: i64,
    old_count: usize,
    new_count: usize,
) -> Result<(), ApiError> {
    let mut fields = Vec::new();
    let mut values = Vec::<Value>::new();
    for (name, old, current) in [
        ("rating", Some(player.rating), total_rating),
        ("maimai_new_rating", Some(player.new_rating), new_rating),
        ("maimai_legacy_count", player.old_count, old_count as i64),
        ("maimai_new_count", player.new_count, new_count as i64),
    ] {
        if old != Some(current) {
            fields.push(format!("`{name}`=?"));
            values.push(current.into());
        }
    }
    let now = chrono::Utc::now().timestamp();
    if !fields.is_empty() || now - player.access_time >= ACCESS_TIME_WRITE_INTERVAL_SECONDS {
        fields.push("access_time=?".into());
        values.push(now.into());
        player.access_time = now;
    }
    if !fields.is_empty() {
        values.push(player.id.into());
        let mut connection = state.pool.get_conn().await?;
        connection
            .exec_drop(
                format!("UPDATE player SET {} WHERE id=?", fields.join(",")),
                values,
            )
            .await?;
    }
    player.rating = total_rating;
    player.new_rating = new_rating;
    player.old_count = Some(old_count as i64);
    player.new_count = Some(new_count as i64);
    Ok(())
}
