-- ============================================================
-- NETFLIX DATA SQL ANALYTICS PROJECT
-- File: Database_setup.sql
-- Purpose: Create database, tables, and load data
-- Source CSV: netflix_titles.csv (Kaggle)
-- ============================================================

CREATE DATABASE netflix_db;
USE netflix_db;

-- ------------------------------------------------------------
-- staging_titles (raw landing table, keeps listed_in / cast /
-- duration / rating as text so we can clean before typing them)
-- ------------------------------------------------------------
CREATE TABLE staging_titles (
    show_id       VARCHAR(10),
    type          VARCHAR(10),
    title         VARCHAR(255),
    director      VARCHAR(255),
    cast_list     TEXT,
    country       VARCHAR(255),
    date_added    VARCHAR(30),
    release_year  INT,
    rating        VARCHAR(20),
    duration      VARCHAR(20),
    listed_in     VARCHAR(500),
    description   TEXT
);

-- ------------------------------------------------------------
-- titles (cleaned, typed)
-- ------------------------------------------------------------
CREATE TABLE titles (
    show_id           VARCHAR(10) PRIMARY KEY,
    type              VARCHAR(10),
    title             VARCHAR(255),
    director          VARCHAR(255),
    country           VARCHAR(255),
    date_added        DATE,
    release_year      INT,
    rating            VARCHAR(10),
    duration_minutes  INT,
    duration_seasons  INT,
    description       TEXT
);

-- ------------------------------------------------------------
-- genres  (from listed_in, many-to-many with titles)
-- ------------------------------------------------------------
CREATE TABLE genres (
    genre_id    INT AUTO_INCREMENT PRIMARY KEY,
    genre_name  VARCHAR(100) UNIQUE
);

CREATE TABLE title_genres (
    show_id   VARCHAR(10),
    genre_id  INT,
    PRIMARY KEY (show_id, genre_id),
    FOREIGN KEY (show_id) REFERENCES titles(show_id),
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id)
);

-- ------------------------------------------------------------
-- actors  (from cast, many-to-many with titles)
-- ------------------------------------------------------------
CREATE TABLE actors (
    actor_id    INT AUTO_INCREMENT PRIMARY KEY,
    actor_name  VARCHAR(150) UNIQUE
);

CREATE TABLE title_actors (
    show_id   VARCHAR(10),
    actor_id  INT,
    PRIMARY KEY (show_id, actor_id),
    FOREIGN KEY (show_id) REFERENCES titles(show_id),
    FOREIGN KEY (actor_id) REFERENCES actors(actor_id)
);


-- ============================================================
-- NETFLIX DATA SQL ANALYTICS PROJECT
-- Purpose: Load CSV into staging, clean it, then populate
--          all normalized tables
-- ============================================================

USE netflix_db;

-- ------------------------------------------------------------
-- 1. Load raw CSV into staging_titles
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/netflix_titles.csv'
INTO TABLE staging_titles
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(show_id, type, title, director, cast_list, country, date_added,
 release_year, rating, duration, listed_in, description);

SELECT COUNT(*) AS staging_count FROM staging_titles;

-- ------------------------------------------------------------
-- 1a. Data-quality fix: a handful of rows (e.g. the
-- "Louis C.K." stand-up specials) have the duration value
-- ("74 min") sitting in the `rating` column by mistake, with
-- `duration` left blank. Swap them back before typing the columns.
-- ------------------------------------------------------------
UPDATE staging_titles
SET
    duration = rating,
    rating   = NULL
WHERE rating LIKE '%min%' AND (duration IS NULL OR duration = '');

-- ------------------------------------------------------------
-- 2. titles (parse date, split duration by type, null-safe)
-- ------------------------------------------------------------
INSERT INTO titles
SELECT
    show_id,
    type,
    title,
    NULLIF(director, ''),
    NULLIF(country, ''),
    STR_TO_DATE(TRIM(NULLIF(date_added, '')), '%M %e, %Y'),
    release_year,
    NULLIF(rating, ''),
    CASE WHEN type = 'Movie'  THEN CAST(SUBSTRING_INDEX(duration, ' ', 1) AS UNSIGNED) END,
    CASE WHEN type = 'TV Show' THEN CAST(SUBSTRING_INDEX(duration, ' ', 1) AS UNSIGNED) END,
    description
FROM staging_titles;

SELECT COUNT(*) AS titles_count FROM titles;

-- ------------------------------------------------------------
-- 3. genres + title_genres (split listed_in via recursive CTE)
-- ------------------------------------------------------------
CREATE TEMPORARY TABLE staging_genres AS
WITH RECURSIVE split_genres AS (
    SELECT
        show_id,
        TRIM(SUBSTRING_INDEX(listed_in, ',', 1)) AS genre_name,
        CASE WHEN LOCATE(',', listed_in) > 0
             THEN SUBSTRING(listed_in, LOCATE(',', listed_in) + 1)
             ELSE NULL END AS remaining
    FROM staging_titles
    UNION ALL
    SELECT
        show_id,
        TRIM(SUBSTRING_INDEX(remaining, ',', 1)),
        CASE WHEN LOCATE(',', remaining) > 0
             THEN SUBSTRING(remaining, LOCATE(',', remaining) + 1)
             ELSE NULL END
    FROM split_genres
    WHERE remaining IS NOT NULL
)
SELECT show_id, genre_name FROM split_genres WHERE genre_name <> '';

INSERT INTO genres (genre_name)
SELECT DISTINCT genre_name FROM staging_genres;

INSERT INTO title_genres (show_id, genre_id)
SELECT sg.show_id, g.genre_id
FROM staging_genres sg
JOIN genres g ON g.genre_name = sg.genre_name;

DROP TEMPORARY TABLE staging_genres;

SELECT COUNT(*) AS genres_count FROM genres;
SELECT COUNT(*) AS title_genres_count FROM title_genres;

-- ------------------------------------------------------------
-- 4. actors + title_actors (split cast via recursive CTE)
-- Rows with no cast listed are skipped (NULLIF / empty check).
-- ------------------------------------------------------------
CREATE TEMPORARY TABLE staging_actors AS
WITH RECURSIVE split_actors AS (
    SELECT
        show_id,
        TRIM(SUBSTRING_INDEX(cast_list, ',', 1)) AS actor_name,
        CASE WHEN LOCATE(',', cast_list) > 0
             THEN SUBSTRING(cast_list, LOCATE(',', cast_list) + 1)
             ELSE NULL END AS remaining
    FROM staging_titles
    WHERE cast_list IS NOT NULL AND cast_list <> ''
    UNION ALL
    SELECT
        show_id,
        TRIM(SUBSTRING_INDEX(remaining, ',', 1)),
        CASE WHEN LOCATE(',', remaining) > 0
             THEN SUBSTRING(remaining, LOCATE(',', remaining) + 1)
             ELSE NULL END
    FROM split_actors
    WHERE remaining IS NOT NULL
)
SELECT show_id, actor_name FROM split_actors WHERE actor_name <> '';

INSERT INTO actors (actor_name)
SELECT DISTINCT actor_name FROM staging_actors;

INSERT INTO title_actors (show_id, actor_id)
SELECT sa.show_id, a.actor_id
FROM staging_actors sa
JOIN actors a ON a.actor_name = sa.actor_name;

DROP TEMPORARY TABLE staging_actors;

SELECT COUNT(*) AS actors_count FROM actors;
SELECT COUNT(*) AS title_actors_count FROM title_actors;

-- ------------------------------------------------------------
-- FINAL VERIFICATION: run this to confirm everything loaded
-- ------------------------------------------------------------
SELECT 'staging_titles' AS table_name, COUNT(*) AS row_count FROM staging_titles
UNION ALL SELECT 'titles', COUNT(*) FROM titles
UNION ALL SELECT 'genres', COUNT(*) FROM genres
UNION ALL SELECT 'title_genres', COUNT(*) FROM title_genres
UNION ALL SELECT 'actors', COUNT(*) FROM actors
UNION ALL SELECT 'title_actors', COUNT(*) FROM title_actors;
