# Scottbot - Discord Funtimes
### This is a bot for personal use. Feel free to take and modify as-needed
##### Before Using:
Place the newest [MTGJson AtomicCards.json](https://mtgjson.com/api/v5/AtomicCards.json) in ./utilities/edh\_maker/

Install thefuzz with `python3 -m pip install thefuzz`

Optional but recommended for performance purposes: `python3 -m pip install python-Levenshtein`

We also need Discord.py (obviously) with `python3 -m pip install discord`


The OS module expects linux and the `fortune` bash command installed.

Note this is developed for python 3.9, and previous versions are not guarunteed.

Create a .env with the DISCORD\_TOKEN environment variable set with your api to get it up and running.

I suggest not using the utilities/gameslistutils.py as it is for personal use. There is also a reference to oscommands.py which just runs fortune, if your machine has it.

## License

MIT License

Copyright (c) 2022 Scott Pomerville

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
