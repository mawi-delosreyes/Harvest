CREATE TABLE User (
	user_id INTEGER(11) NOT NULL AUTO_INCREMENT,
	name VARCHAR(50),
	api_key VARCHAR(50) NOT NULL,
	take_profit INTEGER(3) NOT NULL,
	stop_loss INTEGER(3) NOT NULL,
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

CREATE TABLE XRP_SMA(
	id INTEGER(11) NOT NULL,
	sma_fast DECIMAL(16,6),
	sma_slow DECIMAL(16,6),
	PRIMARY KEY(id)
);

CREATE TABLE XRP_MACD(
	id INTEGER(11) NOT NULL,
	ema_fast DECIMAL(16,6),
	ema_slow DECIMAL(16,6),
	macd DECIMAL(16,6),
	signal_line DECIMAL(16,6),
	PRIMARY KEY(id)
);

CREATE TABLE XRP_ADX(
	id INTEGER(11) NOT NULL,
	atr DECIMAL(16,6),
	plus_di DECIMAL(16,6),
	minus_di DECIMAL(16,6),
	adx DECIMAL(16,6),
	PRIMARY KEY(id)
);