# InspireWorks IVR Demo

Simple Flask + Plivo demo that makes outbound calls and provides a small IVR (language selection, play audio, transfer to an associate).

This repository contains a minimal Flask app (`app.py`) that uses Plivo to place calls and returns Plivo XML (TwiML-like) responses for IVR flows.

## Recommended Python
- Use Python 3.11 or 3.12 (recommended). Some C extensions like `lxml` may not have wheels for the newest CPython (e.g., 3.14) and will fail to compile on macOS.

## Prerequisites
- macOS (or Linux)
- Python 3.11/3.12 (recommended)
- Git, Homebrew (optional)
- A Plivo account and credentials (AUTH ID and AUTH TOKEN) and a source phone number

## Quick setup
1. Clone the repo (if not already):
   git clone <your-repo>

2. Create a virtual environment (example using system Python or Homebrew installed python@3.11):

```bash
# Example using a Homebrew python@3.11 binary (adjust path if needed)
/opt/homebrew/opt/python@3.11/bin/python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

Note: If `lxml` fails to build on your machine, see "Troubleshooting: lxml build" below.

## Environment variables
Create a `.env` file in the project root with the following values:

```
PLIVO_AUTH_ID=your_plivo_auth_id
PLIVO_AUTH_TOKEN=your_plivo_auth_token
PLIVO_SOURCE_NUMBER=+1xxxxxxxxxx   # the Plivo number that will be used as the caller id
HOST_URL=https://<your-public-host>  # ngrok or public host that Plivo can reach
ASSOCIATE_NUMBER=+11234567890        # optional: default is +11234567890
AUDIO_URL=https://.../audio.mp3      # optional: URL to audio to play
```

The app uses `python-dotenv` to load `.env` automatically.

## Running the app
Start the Flask app (inside your venv):

```bash
python app.py
```

By default Flask serves on port 5000. Visit http://127.0.0.1:5000 and you should see a simple form to place a call.

## Important endpoints (for Plivo)
- `GET /answer` — initial IVR prompt (returns XML with <GetDigits>)
- `POST /ivr/language` — handles language selection and returns next menu
- `POST /ivr/action` — handles action (play audio or dial associate)
- `POST /call` — local form posts to this to trigger an outbound call via the Plivo SDK

When creating a call with Plivo, `answer_url` should point to your publicly reachable `HOST_URL` + `/answer`. If testing locally, use `ngrok http 5000` and put the ngrok URL into `HOST_URL`.

## Testing locally with curl
- Check the root page:

```bash
curl -i http://127.0.0.1:5000/
```

- Check the answer XML (should return `Content-Type: application/xml` and Plivo XML):

```bash
curl -i http://127.0.0.1:5000/answer
```

- Trigger a call from the local form (or use the `/call` endpoint with `curl`):

```bash
curl -X POST -d "to=+1YYYYYYYYYY" http://127.0.0.1:5000/call
```

## Troubleshooting: lxml build on macOS
If `pip install -r requirements.txt` fails building `lxml`:

1. Prefer using Python 3.11 or 3.12 where prebuilt wheels are available.
2. If you must use the system Python or newer Python that lacks wheels, install native build deps:

```bash
# install Xcode command line tools
xcode-select --install

# install libxml2/libxslt and pkg-config via Homebrew
brew install libxml2 libxslt pkg-config

# export flags (adjust prefix for Intel macs where Homebrew is /usr/local)
export LDFLAGS="-L/opt/homebrew/opt/libxml2/lib -L/opt/homebrew/opt/libxslt/lib"
export CPPFLAGS="-I/opt/homebrew/opt/libxml2/include -I/opt/homebrew/opt/libxslt/include"
export PKG_CONFIG_PATH="/opt/homebrew/opt/libxml2/lib/pkgconfig:/opt/homebrew/opt/libxslt/lib/pkgconfig"

pip install -r requirements.txt
```

Even with build deps, some combinations of CPython and lxml versions may not be compatible — using a supported Python version is the most straightforward fix.

## Notes about Plivo XML helper
This app expects a Plivo XML helper (plivoxml). If your installed `plivo` package exposes `plivo.plivoxml`, `app.py` will use it. A small fallback XML builder exists in `app.py` so the endpoints can still produce the minimal XML the app needs.

## Next steps / suggestions
- Add a `.env.example` and `runtime.txt` or CI config to pin Python version.
- Add tests for the IVR XML responses.

## License
MIT
