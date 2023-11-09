CREATE TABLE websources(id BIGSERIAL PRIMARY KEY,reversed_hostname TEXT,link TEXT,mtime INTEGER,content_hash BYTEA,last_indexed_ts INTEGER,last_checked_ts INTEGER,indexer_version INTEGER,resource_content TEXT);
-- reversed_hostname: like com.github.editor
-- link is the web address, mtime is the modification time of the resource, content_hash is a hash to determine if modifications have been made when mtime fails, last_indexed_ts and last_checked_ts are obvious; last_checked_ts is to check things for modifications
-- indexer_version is so that links can be added to the link_queue table if the index method is updated and stuff needs to be reindexed in the new way. No index since any change is likely to need a full table scan or tmpindex anyway
-- resource_content is the text content of the page – perhaps to be changed to BYTEA in future, if non-text resources are required
CREATE UNIQUE INDEX websources_links ON websources(link);
CREATE INDEX websources_timecheck ON websources(last_checked_ts);

CREATE TABLE link_queue(id BIGSERIAL PRIMARY KEY,last_indexed_ts INTEGER,added_ts INTEGER,link TEXT,...
  ,FOREIGN KEY(link) REFERENCES websources(link));
