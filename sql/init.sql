DROP TABLE IF EXISTS total_experiments_per_user;
CREATE TABLE IF NOT EXISTS total_experiments_per_user (
    id SERIAL NOT NULL,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    experiment_qty INT,
    time_stamp TIMESTAMP DEFAULT now(),
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS avg_experiments_amount;
CREATE TABLE IF NOT EXISTS avg_experiments_amount (
    id SERIAL NOT NULL,
    avg_amount FLOAT NOT NULL,
    time_stamp TIMESTAMP DEFAULT now(),
    PRIMARY KEY (id)

);

DROP TABLE IF EXISTS most_experimented_compound;
CREATE TABLE IF NOT EXISTS most_experimented_compound (
    id SERIAL NOT NULL,
    comp_id INT NOT NULL,
    comp_name VARCHAR(100) NOT NULL,
    comp_structure VARCHAR(100) NOT NULL,
    time_stamp TIMESTAMP DEFAULT now(),
    PRIMARY KEY (id)
);
