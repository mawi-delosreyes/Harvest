import numpy as np

class Forecast:
    def __init__(self, data):
        self.data = data 
        self.result = None


    def normalize(self, series):
        s = np.array(series)
        min_val = s.min()
        max_val = s.max()
        normalized = (s - min_val) / (max_val - min_val)
        return normalized, min_val, max_val


    def denormalize(self, norm_series, min_val, max_val):
        return norm_series * (max_val - min_val) + min_val


    def moving_average(self, data, window_size=3):
        return np.convolve(data, np.ones(window_size)/window_size, mode='same')


    def computeForecast(self):
        steps=15
        window=8
        noise_scale=0.3
        freq=4
        phase=6.283185307179586
        smooth_window=3
        
        data = [float(d) for d in self.data]
        data, min_data, max_data = self.normalize(data)

        x = np.arange(window)
        y = data[-window:]
        weights = np.exp(np.linspace(0, 1, window))
        coeffs = np.polyfit(x, y, 3, w=weights)
        trend = np.polyval(coeffs, np.arange(window, window + steps))
        fitted = np.polyval(coeffs, x)
        residuals = y - fitted
        rolling_std = np.std(data[-window:])
        noise_std = np.std(residuals) * (1 + rolling_std)
        
        local_noise_scale = np.interp(
            np.arange(steps), 
            np.linspace(0, steps-1, len(residuals)), 
            np.abs(residuals)
        )
        
        noise = noise_std * noise_scale * local_noise_scale * np.sin(np.arange(steps) * freq + phase)
        forecast = trend * (1 - noise_scale) + (trend + noise) * noise_scale
        forecast = np.maximum(forecast, 0)
        
        if smooth_window > 1:
            forecast = self.moving_average(forecast, window_size=smooth_window)
        
        forecast = self.denormalize(np.array(forecast.tolist()), min_data, max_data)
        self.result = (forecast[0], forecast[-1])
