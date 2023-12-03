-- Change timestamps to millisecond precision 64 bit integers
-- Move web resource contents to separate table, and use resource ID integers instead of link contents in other tables (to reduce size). 

CREATE TABLE websources(id BIGSERIAL PRIMARY KEY,reversed_hostname TEXT,link TEXT,mtime INTEGER,content_hash BYTEA,last_indexed_ts INTEGER,last_checked_ts INTEGER,indexer_version INTEGER,resource_content TEXT);
-- reversed_hostname: like com.github.editor – probably to be used in future for clustering aspirations
-- link is the web address, mtime is the modification time of the resource, content_hash is a hash to determine if modifications have been made when mtime fails, last_indexed_ts and last_checked_ts are obvious; last_checked_ts is to check things for modifications
-- indexer_version is so that links can be added to the link_queue table if the index method is updated and stuff needs to be reindexed in the new way. No index since any change is likely to need a full table scan or tmpindex anyway
-- resource_content is the text content of the page – perhaps to be changed to BYTEA in future, if non-text resources are required
CREATE UNIQUE INDEX websources_links ON websources(link);
CREATE INDEX websources_timecheck ON websources(last_checked_ts);

-- Normalised form violation – I'll try to make it worthwhile
CREATE TABLE link_queue(id BIGSERIAL PRIMARY KEY,last_indexed_ts INTEGER,added_ts INTEGER,link TEXT,claimant_id INTEGER, claim_ts INTEGER,FOREIGN KEY(link) REFERENCES websources(link), FOREIGN KEY(claimant_id) REFERENCES spyders(id));
--
CREATE UNIQUE INDEX link_queue_link_uniqueness ON link_queue(link);
CREATE INDEX link_queue_added_ts ON link_queue(added_ts);
CREATE PARTIAL INDEX link_queue_claims ON link_queue WHERE claimant_id != null; -- Fix this and figure out queries. Also check if it's possible to use the foreign key constraint with a mostly null column, and if so then check if the partial index can be used. 
CREATE PARTIAL INDEX link_queue_claim_ts ON link_queue WHERE claim_ts != null;


CREATE TABLE spyders(id SERIAL PRIMARY KEY, created_ts INTEGER,last_claim_ts INTEGER)
CREATE INDEX spyder_batchtimes ON spyders (last_claim_ts);


CREATE TABLE websource_search(websource_id BIGINT,part INTEGER, text_search TS_VECTOR, PRIMARY KEY(websource_id, part));
-- Add a foreign key, but check if the compound key can be used for that. If not then perhaps no foreign key constraint. 
-- the part column is just so that large output can be split into multiple sections and be reliably ordered – most instances of part will just be 1
