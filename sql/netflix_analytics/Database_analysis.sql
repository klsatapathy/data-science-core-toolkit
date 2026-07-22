/* ============================================================================
   NETFLIX DATA ANALYSIS — SQL ANALYSIS PORTFOLIO
   ============================================================================
   Database      : MySQL 8.0 (MySQL Workbench)
   Dataset       : Netflix Titles Dataset (Kaggle) — normalized into
                   titles, genres, title_genres, actors, title_actors
   Objective     : End-to-end content analysis covering library growth,
                   genre trends, geography, cast/director patterns, and
                   ratings/duration behavior.
   ============================================================================ */


/* ============================================================================
   SECTION A — CONTENT TRENDS
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- A1. Movie vs TV Show Split
-- ----------------------------------------------------------------------------
SELECT
    type,
    COUNT(*) AS title_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM titles), 2) AS pct_of_total
FROM titles
GROUP BY type
ORDER BY title_count DESC;

/* INSIGHT A1 — Movies dominate the library: 6,131 titles (69.62%) vs 2,676 TV Shows (30.38%).
Netflix's catalog is roughly 7:3 movie-heavy — TV Shows are the minority format by a wide margin,
even though streaming is often associated with binge-worthy series. */


-- ----------------------------------------------------------------------------
-- A2. Content Added by Year & Type (Library Growth Trend)
-- ----------------------------------------------------------------------------
SELECT
    YEAR(date_added) AS year_added,
    type,
    COUNT(*) AS title_count
FROM titles
WHERE date_added IS NOT NULL
GROUP BY year_added, type
ORDER BY year_added, type;

/* INSIGHT A2 — Explosive growth 2016-2019, then a pullback. Titles added per year jumped from
429 (2016) to 1,188 (2017) to 1,649 (2018) to a peak of 2,016 (2019) — a >4x increase in 3 years.
2020 (1,879) and 2021 (1,498) both declined from the 2019 peak — content acquisition slowed,
likely tied to pandemic-era production shutdowns. TV Shows grew faster proportionally: TV Show
share of yearly additions rose from ~18% (2016) to ~34% (2021), so while movies still dominate
the total catalog, TV Shows are an increasing share of what's newly added. */


-- ----------------------------------------------------------------------------
-- A3. Release-to-Addition Gap by Type (How "Fresh" Is Netflix's Content?)
-- ----------------------------------------------------------------------------
SELECT
    type,
    ROUND(AVG(YEAR(date_added) - release_year), 2) AS avg_years_gap
FROM titles
WHERE date_added IS NOT NULL
GROUP BY type;

/* INSIGHT A3 — TV Shows are added far fresher than Movies. Average gap between release year and
Netflix add date is 5.73 years for Movies vs just 2.30 years for TV Shows — less than half.
Netflix is more of a back-catalog library for film, but stays closer to "current" for series —
consistent with licensing fresh seasons quickly while movies rely more on older catalog deals. */


-- ----------------------------------------------------------------------------
-- A4. Content Added by Month (Release Seasonality)
-- ----------------------------------------------------------------------------
SELECT
    MONTHNAME(date_added) AS month_added,
    COUNT(*) AS title_count
FROM titles
WHERE date_added IS NOT NULL
GROUP BY month_added
ORDER BY title_count DESC;

/* INSIGHT A4 — July (827) and December (813) are the top 2 months for adding content — both
align with school holidays / year-end viewing spikes. February is the clear low point (563),
nearly 32% below July — the shortest month also gets the least new content, whether by
calendar-day effect or a deliberate lighter release slate. */


/* ============================================================================
   SECTION B — GENRE ANALYSIS
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- B1. Top Genres by Title Count
-- ----------------------------------------------------------------------------
SELECT
    g.genre_name,
    COUNT(*) AS title_count
FROM title_genres tg
JOIN genres g ON tg.genre_id = g.genre_id
GROUP BY g.genre_name
ORDER BY title_count DESC
LIMIT 10;

/* INSIGHT B1 — "International Movies" is the single biggest genre tag (2,752 titles), ahead of
Dramas (2,427) and Comedies (1,674). Since titles carry multiple genre tags, this reflects how
heavily Netflix leans on "International" as a catch-all label for its non-US-origin catalog —
it appears on nearly 1 in 3 titles overall. */


-- ----------------------------------------------------------------------------
-- B2. Genre Evolution — Average Release Year per Genre (Window: implicit via HAVING)
-- ----------------------------------------------------------------------------
SELECT
    g.genre_name,
    COUNT(*) AS title_count,
    ROUND(AVG(t.release_year), 1) AS avg_release_year
FROM title_genres tg
JOIN genres g ON tg.genre_id = g.genre_id
JOIN titles t ON tg.show_id = t.show_id
GROUP BY g.genre_name
HAVING COUNT(*) >= 100
ORDER BY avg_release_year;

/* INSIGHT B2 — "Action & Adventure" is the oldest-skewing major genre (avg release year 2009.5),
while "TV Dramas" and "International TV Shows" skew newest (avg 2017.2 and 2017.0). This lines up
with A1/A3 — TV content on Netflix is systematically newer than movie content, and that pattern
holds at the genre level too, not just the type level. */


-- ----------------------------------------------------------------------------
-- B3. Genre Mix: Top 5 Genres for Movies vs TV Shows (Window Function: RANK)
-- ----------------------------------------------------------------------------
WITH genre_by_type AS (
    SELECT
        t.type,
        g.genre_name,
        COUNT(*) AS title_count,
        RANK() OVER (PARTITION BY t.type ORDER BY COUNT(*) DESC) AS rnk
    FROM title_genres tg
    JOIN genres g ON tg.genre_id = g.genre_id
    JOIN titles t ON tg.show_id = t.show_id
    GROUP BY t.type, g.genre_name
)
SELECT type, genre_name, title_count
FROM genre_by_type
WHERE rnk <= 5
ORDER BY type, rnk;

/* INSIGHT B3 — Movies and TV Shows have almost no genre overlap in their top 5. Movies are led
by International Movies (2,752), Dramas (2,427), Comedies (1,674), Documentaries (869), and
Action & Adventure (859). TV Shows are led by International TV Shows (1,351), TV Dramas (763),
TV Comedies (581), Crime TV Shows (470), and Kids' TV (451) — completely separate genre
vocabularies, which matches how Netflix tags TV-specific vs Movie-specific categories. */


-- ----------------------------------------------------------------------------
-- B4. Early vs Recent Genre Focus — Pre-2018 vs 2018+ Additions (Window: RANK)
-- ----------------------------------------------------------------------------
WITH era_genre AS (
    SELECT
        CASE WHEN YEAR(t.date_added) < 2018 THEN 'Pre-2018' ELSE '2018 & Later' END AS era,
        g.genre_name,
        COUNT(*) AS title_count,
        RANK() OVER (
            PARTITION BY CASE WHEN YEAR(t.date_added) < 2018 THEN 'Pre-2018' ELSE '2018 & Later' END
            ORDER BY COUNT(*) DESC
        ) AS rnk
    FROM title_genres tg
    JOIN genres g ON tg.genre_id = g.genre_id
    JOIN titles t ON tg.show_id = t.show_id
    WHERE t.date_added IS NOT NULL
    GROUP BY era, g.genre_name
)
SELECT era, genre_name, title_count
FROM era_genre
WHERE rnk <= 5
ORDER BY era, rnk;

/* INSIGHT B4 — The top genre is stable over time (International Movies leads both eras), but
"Action & Adventure" breaks into the recent top-5 (741 titles, 2018+) while it wasn't a
pre-2018 leader — suggesting a deliberate content-strategy shift toward action content as
Netflix scaled up its catalog after 2018. */


/* ============================================================================
   SECTION C — COUNTRY & GEOGRAPHY
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- C1. Top Content-Producing Countries (Primary Country)
-- ----------------------------------------------------------------------------
SELECT
    SUBSTRING_INDEX(country, ',', 1) AS primary_country,
    COUNT(*) AS title_count
FROM titles
WHERE country IS NOT NULL
GROUP BY primary_country
ORDER BY title_count DESC
LIMIT 10;

/* INSIGHT C1 — United States (3,211) and India (1,008) are the two dominant content origins by
far, together accounting for over half of all titles with a known country. United Kingdom
(628) is a distant third. This is a heavily US/India-concentrated catalog, not a globally
even spread across the ~86 countries represented. */


-- ----------------------------------------------------------------------------
-- C2. Movie/TV Ratio by Top Countries
-- ----------------------------------------------------------------------------
WITH top_countries AS (
    SELECT SUBSTRING_INDEX(country, ',', 1) AS primary_country
    FROM titles
    WHERE country IS NOT NULL
    GROUP BY primary_country
    ORDER BY COUNT(*) DESC
    LIMIT 8
)
SELECT
    SUBSTRING_INDEX(t.country, ',', 1) AS primary_country,
    t.type,
    COUNT(*) AS title_count
FROM titles t
WHERE SUBSTRING_INDEX(t.country, ',', 1) IN (SELECT primary_country FROM top_countries)
GROUP BY primary_country, t.type
ORDER BY primary_country, t.type;

/* INSIGHT C2 — India is the most movie-skewed major country (92.0% Movie / 927 vs 81 TV Shows) —
almost no TV Show presence. South Korea (22.3% movie) and Japan (32.8% movie) sit at the exact
opposite end — both are TV/anime-heavy catalogs. The US (73.6% movie) and UK (60.8% movie) fall
in between, closer to the global average, showing this isn't just a "movies dominate everywhere"
pattern — it varies sharply by country of origin. */


-- ----------------------------------------------------------------------------
-- C3. Top Genre per Top-5 Country (Window Function: RANK)
-- ----------------------------------------------------------------------------
WITH top5_countries AS (
    SELECT SUBSTRING_INDEX(country, ',', 1) AS primary_country
    FROM titles
    WHERE country IS NOT NULL
    GROUP BY primary_country
    ORDER BY COUNT(*) DESC
    LIMIT 5
),
country_genre AS (
    SELECT
        SUBSTRING_INDEX(t.country, ',', 1) AS primary_country,
        g.genre_name,
        COUNT(*) AS title_count,
        RANK() OVER (
            PARTITION BY SUBSTRING_INDEX(t.country, ',', 1)
            ORDER BY COUNT(*) DESC
        ) AS rnk
    FROM titles t
    JOIN title_genres tg ON t.show_id = tg.show_id
    JOIN genres g ON tg.genre_id = g.genre_id
    WHERE SUBSTRING_INDEX(t.country, ',', 1) IN (SELECT primary_country FROM top5_countries)
    GROUP BY primary_country, g.genre_name
)
SELECT primary_country, genre_name, title_count
FROM country_genre
WHERE rnk <= 3
ORDER BY primary_country, rnk;

/* INSIGHT C3 — India's #1 genre is International Movies (845) — its own domestic output is
tagged as "international" from Netflix's (US-centric) catalog perspective. Japan's top genre
is International TV Shows (144), closely followed by Anime Series (136) — anime is a
near-equal pillar of its catalog, not a side category. The UK stands out as the only top-5
country whose #1 genre is a country-specific tag (British TV Shows, 216) rather than a generic
Drama/International label — a distinct enough catalog to earn its own tag. */


-- ----------------------------------------------------------------------------
-- C4. Single-Country vs Co-Production Titles
-- ----------------------------------------------------------------------------
SELECT
    CASE WHEN country LIKE '%,%' THEN 'Co-production (2+ countries)' ELSE 'Single country' END AS production_type,
    COUNT(*) AS title_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM titles WHERE country IS NOT NULL), 2) AS pct_of_total
FROM titles
WHERE country IS NOT NULL
GROUP BY production_type;

/* INSIGHT C4 — Co-productions are a minority but not negligible: 1,320 titles (16.55%) list 2+
countries, vs 83.45% single-country. Among co-produced titles, the US appears as a partner
country most often (393 titles) — even when it's not the sole country of origin, American
studios/distributors are frequently involved behind the scenes. */


/* ============================================================================
   SECTION D — ACTOR & DIRECTOR ANALYSIS
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- D1. Top Directors by Title Count
-- ----------------------------------------------------------------------------
SELECT
    director,
    COUNT(*) AS title_count
FROM titles
WHERE director IS NOT NULL
GROUP BY director
ORDER BY title_count DESC
LIMIT 10;

/* INSIGHT D1 — Rajiv Chilaka leads with 19 titles, almost all Indian animated/children's content —
ahead of Raúl Campos & Jan Suter (18, a directing duo credited jointly) and Suhas Kadav (16).
Notably, none of the most "famous" Hollywood names top the list by volume — the top spots go to
high-output regional/children's-content directors, not prestige filmmakers, since this ranks by
title count rather than acclaim. */


-- ----------------------------------------------------------------------------
-- D2. Top Actors by Title Count
-- ----------------------------------------------------------------------------
SELECT
    a.actor_name,
    COUNT(*) AS title_count
FROM title_actors ta
JOIN actors a ON ta.actor_id = a.actor_id
GROUP BY a.actor_name
ORDER BY title_count DESC
LIMIT 10;

/* INSIGHT D2 — Anupam Kher tops the actor list with 43 titles, and Bollywood names dominate the
top 10 overall (Shah Rukh Khan 35, Naseeruddin Shah 32, Akshay Kumar 30, Om Puri 30, Amitabh
Bachchan 28) alongside Japanese voice actors (Takahiro Sakurai 32, Yuki Kaji 29) from anime
series. This mirrors C1's finding — India's outsized share of the catalog surfaces again here,
this time in cast credits rather than country tags. */


-- ----------------------------------------------------------------------------
-- D3. Director-Actor Frequent Collaborations
-- ----------------------------------------------------------------------------
SELECT
    t.director,
    a.actor_name,
    COUNT(*) AS collab_count
FROM titles t
JOIN title_actors ta ON t.show_id = ta.show_id
JOIN actors a ON ta.actor_id = a.actor_id
WHERE t.director IS NOT NULL
GROUP BY t.director, a.actor_name
ORDER BY collab_count DESC
LIMIT 10;

/* INSIGHT D3 — Rajiv Chilaka's regular voice-cast (Julie Tejwani, Jigna Bhardwaj, Rajesh Kava —
17 titles each) shows a tight, repeat production team typical of long-running animated series,
not one-off film casts. This is a completely different collaboration pattern from the
Movies/Dramas world (no single Hollywood director-actor pair even approaches these numbers) —
recurring animated series inflate collaboration counts far more than feature films do. */


-- ----------------------------------------------------------------------------
-- D4. Top-5 Directors — Type & Country Focus
-- ----------------------------------------------------------------------------
SELECT
    t.director,
    SUBSTRING_INDEX(t.country, ',', 1) AS primary_country,
    COUNT(*) AS title_count,
    SUM(CASE WHEN t.type = 'Movie' THEN 1 ELSE 0 END) AS movies,
    SUM(CASE WHEN t.type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows
FROM titles t
WHERE t.director IN (
    SELECT director FROM titles WHERE director IS NOT NULL
    GROUP BY director ORDER BY COUNT(*) DESC LIMIT 5
)
GROUP BY t.director, primary_country
ORDER BY title_count DESC;

/* INSIGHT D4 — All 5 top directors are 100% Movie directors — none of them have a single TV
Show credit in the dataset. Rajiv Chilaka and Suhas Kadav are both India-based (19 and 16
titles respectively), while Raúl Campos/Jan Suter (Mexico) and Marcus Raboy/Jay Karas (United
States) round out the list — the most prolific directors cluster in comedy-special and
animated-film production, a very different profile from prestige feature directing. */


/* ============================================================================
   SECTION E — RATINGS & DURATION
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- E1. Content Rating Distribution
-- ----------------------------------------------------------------------------
SELECT
    rating,
    COUNT(*) AS title_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM titles WHERE rating IS NOT NULL), 2) AS pct_of_total
FROM titles
WHERE rating IS NOT NULL
GROUP BY rating
ORDER BY title_count DESC;

/* INSIGHT E1 — TV-MA is the single largest rating (3,207 titles, 36.44%) — more than a third of
the entire catalog is mature-audience content. TV-MA + TV-14 combined = 61% of all titles —
Netflix's catalog leans heavily toward teen/adult content rather than family-friendly fare;
G/TV-Y/TV-Y7 family-safe ratings combined make up well under 10% of the library. */


-- ----------------------------------------------------------------------------
-- E2. Average Movie Duration Trend by Decade
-- ----------------------------------------------------------------------------
SELECT
    CASE
        WHEN release_year < 2000 THEN 'Pre-2000'
        WHEN release_year BETWEEN 2000 AND 2009 THEN '2000s'
        WHEN release_year BETWEEN 2010 AND 2019 THEN '2010s'
        ELSE '2020+'
    END AS decade,
    COUNT(*) AS movie_count,
    ROUND(AVG(duration_minutes), 1) AS avg_duration_minutes
FROM titles
WHERE type = 'Movie' AND duration_minutes IS NOT NULL
GROUP BY decade
ORDER BY decade;

/* INSIGHT E2 — Movies have gotten steadily shorter every decade: Pre-2000 averaged 114.97 min,
dropping to 112.11 min (2000s), 96.91 min (2010s), and just 93.64 min (2020+) — a ~20% reduction
from pre-2000 levels. This aligns with the broader streaming-era trend toward shorter runtimes
optimized for attention spans and algorithmic recommendation, not a one-off dip. */


-- ----------------------------------------------------------------------------
-- E3. TV Show Seasons Distribution
-- ----------------------------------------------------------------------------
SELECT
    duration_seasons,
    COUNT(*) AS show_count
FROM titles
WHERE type = 'TV Show' AND duration_seasons IS NOT NULL
GROUP BY duration_seasons
ORDER BY duration_seasons;

/* INSIGHT E3 — 67% of all TV Shows on Netflix have only 1 season (1,793 of 2,676) — the vast
majority never get renewed past their first season, or are limited series by design. Shows
with 5+ seasons make up a small tail (fewer than 5% combined) — long-running multi-season
series are the exception, not the norm, on this platform. */


-- ----------------------------------------------------------------------------
-- E4. Duration Extremes by Genre — Longest & Shortest Average Movie Runtime
-- ----------------------------------------------------------------------------
WITH movie_genre_duration AS (
    SELECT
        g.genre_name,
        COUNT(*) AS movie_count,
        ROUND(AVG(t.duration_minutes), 1) AS avg_duration_minutes
    FROM titles t
    JOIN title_genres tg ON t.show_id = tg.show_id
    JOIN genres g ON tg.genre_id = g.genre_id
    WHERE t.type = 'Movie' AND t.duration_minutes IS NOT NULL
    GROUP BY g.genre_name
    HAVING COUNT(*) >= 20
)
(SELECT genre_name, movie_count, avg_duration_minutes, 'Longest' AS category
 FROM movie_genre_duration ORDER BY avg_duration_minutes DESC LIMIT 5)
UNION ALL
(SELECT genre_name, movie_count, avg_duration_minutes, 'Shortest' AS category
 FROM movie_genre_duration ORDER BY avg_duration_minutes ASC LIMIT 5);

/* INSIGHT E4 — Classic Movies run longest on average (118.6 min), followed by Action & Adventure
(113.5 min) and Dramas (113.1 min) — genres built around extended narrative or spectacle.
Stand-Up Comedy is the shortest major genre (67.3 min) after the tiny "Movies" catch-all tag —
comedy specials are structurally built to run under 90 minutes, nearly 40% shorter than the
overall movie average (99.6 min). */

/* ============================================================================
   END OF SCRIPT — 20 BUSINESS INSIGHTS ACROSS 5 ANALYTICAL AREAS
   ============================================================================
   A. Content Trends       -> Insights A1, A2, A3, A4
   B. Genre Analysis        -> Insights B1, B2, B3, B4
   C. Country & Geography   -> Insights C1, C2, C3, C4
   D. Actor & Director      -> Insights D1, D2, D3, D4
   E. Ratings & Duration    -> Insights E1, E2, E3, E4
   ============================================================================ */
