# Hero ranking system for *Honor of the King*

![ ](/1350res/中路_1350_plot.png)

A hero ranking system for *Honor of the King*, the popular MOBA game in China.
The game is going to be made available worldwide soon.

This project proposes a mathematical model to combine win rate, pick rate and ban rate of a hero into a score that reflects their comprehensive performance among a particular group of players. A related system for LoL is [here](https://www.mobachampion.com/tier-list/).

The code `get_rank_fitted.py` retrieves data from [苏苏的荣耀助手](https://pvp.91m.top), does the calculation and renders posters, charts and data tables (in the `res` and `1350res` folders) for visualization. **You need an account of the data platform to run the code; edit the `openId` and `accessToken` in the code as yours.**

Python packages required:
- `pandas >= 1.3.1`
- `numpy >= 1.20.3`
- `matplotlib >= 3.4.2`
- `imgkit >= 1.2.2`
- `pillow >= 8.3.1`

For mathematical details, see the docs in the repo (in Chinese).

The font used in rendering is [Aa翰林楷体](https://font.chinaz.com/220408328300.htm).
