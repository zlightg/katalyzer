CREATE TABLE IF NOT EXISTS user_info (
    id                  SERIAL PRIMARY KEY,
    hash_lookup         UUID,
    date_added          timestamp  default now,
    last_modified       timestamp default now()
);

CREATE TABLE IF NOT EXISTS preference (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(255),
    date_added          timestamp,
    last_modified       timestamp default now()
);

CREATE TABLE IF NOT EXISTS user_preference (
    user_id             INT,
    preference_id       INT,
    date_added          timestamp,
    last_modified       timestamp default now(),
    CONSTRAINT fk_user
        FOREIGN KEY(user_id)
	        REFERENCES user_info(id),
    CONSTRAINT fk_preference
        FOREIGN KEY(preference_id)
            REFERENCES preference(id)
);

CREATE TABLE IF NOT EXISTS feeling (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(1024),
    date_added          timestamp,
    last_modified       timestamp default now()
);

CREATE TABLE IF NOT EXISTS activity (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(1024),
    date_added          timestamp,
    last_modified       timestamp default now()
);

-- Create message state to track where the conversation is at
CREATE TABLE IF NOT EXISTS message_state (
    id                  SERIAL PRIMARY KEY,
    state               VARCHAR(1024),
    category            VARCHAR(1024),
    message_template    TEXT,
    pre_message_processor  TEXT,
    post_message_processor TEXT,
    next_state_id_func  TEXT,
    options             TEXT,
    date_added          timestamp,
    last_modified       timestamp default now(),
    CONSTRAINT fk_state
        FOREIGN KEY(next_state)
	        REFERENCES message_state(id)
);

CREATE TABLE IF NOT EXISTS cool_down (
    id                  SERIAL PRIMARY KEY,
    cool_down_interval  INTERVAL,
    cool_down_message   TEXT,
    message_state       Int,
    date_added          timestamp default now(),
    last_modified       timestamp default now(),
    CONSTRAINT fk_message_state
        FOREIGN KEY(message_state)
            REFERENCES message_state(id)
);

CREATE TABLE IF NOT EXISTS conversation (
    id                  SERIAL PRIMARY KEY,
    human_user_id       INT,
    model_user_id       INT,
    CONSTRAINT fk_human_user
        FOREIGN KEY(human_user_id)
	        REFERENCES user_info(id),
	CONSTRAINT fk_model_user
        FOREIGN KEY(model_user_id)
	        REFERENCES user_info(id),
    date_added          timestamp,
    last_modified       timestamp default now()
);

CREATE TABLE IF NOT EXISTS message (
    id                  SERIAL PRIMARY KEY,
    conversation_id     INT,
    sender_id           INT,
    state_id            INT,
    message             TEXT,
    persisted_state     TEXT,
    sent_at             timestamp default now(),
    CONSTRAINT fk_conversation
        FOREIGN KEY(conversation_id)
	        REFERENCES conversation(id),
    CONSTRAINT fk_sender
        FOREIGN KEY(sender_id)
	        REFERENCES user_info(id),
	CONSTRAINT fk_state
        FOREIGN KEY(state_id)
	        REFERENCES message_state(id)
);

CREATE INDEX idx_cool_down_message_state on cool_down(message_state);
CREATE INDEX idx_conversation_human_id on conversation(human_user_id);
CREATE INDEX idx_message_timestamp on message(sent_at);
CREATE INDEX idx_message_conversation_id on message(conversation_id);




