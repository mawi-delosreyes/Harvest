CREATE TABLE User (
	user_id INTEGER(11) NOT NULL AUTO_INCREMENT,
	name VARCHAR(50),
	hold TINYINT(1),
	PRIMARY KEY (user_id)
);

CREATE TABLE Daily_Balance (
	timestamp DATETIME,
	user_id INTEGER(11) NOT NULL,
	balance DECIMAL(16,6)
);

CREATE TABLE Cryptocurrency(
	crypto_id INTEGER(11) NOT NULL AUTO_INCREMENT,
	crypto_name VARCHAR(50) NOT NULL,
	crypto_pair VARCHAR(50),
	user_id INTEGER(11) NOT NULL,
	take_profit DECIMAL(16,6),
	stop_loss DECIMAL(16,6),
	hold TINYINT(1),
	PRIMARY KEY(crypto_id)
);

CREATE TABLE XRP(
	id INTEGER(11) NOT NULL AUTO_INCREMENT,
	open_timestamp DATETIME,
	open DECIMAL(16,6),
	high DECIMAL(16,6),
	low DECIMAL(16,6),
	close DECIMAL(16,6),
	volume DECIMAL(16,6),
	close_timestamp DATETIME,
	quote_asset_volume DECIMAL(16,6),
	num_trades INTEGER(11),
	PRIMARY KEY(id)
);
