# ETF Rotation Strategy Backtesting Framework
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-360/)
![License](https://img.shields.io/github/license/AI4Finance-Foundation/fingpt.svg?color=brightgreen)

This Python framework is a one-stop solution for backtesting ETF rotation strategies. It aims to be efficient, flexible, and user-friendly for both beginners and seasoned traders.

# __Key Features__

1.Historical Data Included: The framework comes with all necessary historical data for backtesting, saving users the time and effort of collecting data independently.

2.Plug and Play: The framework is ready to use out of the box. Just fill out the configuration file, and you can start running backtests instantly.

3.Extensible Factors and Strategies: Our framework encourages innovation, allowing users to freely extend factors and strategies.

Leverage this robust platform to model, validate, and optimize your investment strategies today.

# __Install__

After downloading and extracting, switch to the project directory.
```shell
pip install -r requirements.txt
```

# __Demo__

1.In "config.py", you can add ETF candidates to the ETF rotation pool.

2.In the "factor" folder, you can freely add various factors, and in the "strategy" folder, you can freely add rotation algorithms.

3.Run "main.py", after which a strategy report in HTML format can be generated.

![Example Image](https://github.com/chrisphoenixsoar/etf_rotation/blob/master/demo.png)
