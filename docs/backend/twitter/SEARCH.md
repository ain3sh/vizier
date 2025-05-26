# 🔍 Twitter Advanced Search — Ultimate Guide

**A comprehensive reference for mastering Twitter’s powerful advanced search capabilities.**

This guide brings together the **full scope of Twitter’s advanced search syntax**, including **undocumented search operators** and **behavioral quirks**, optimized for:

- 🔍 **Power users**
- 🧵 **Researchers**
- 📊 **Developers**
- 📢 **Marketers**
- 🧠 **Data Scientists**

It applies to:

- [Twitter Web Search](https://twitter.com/search-advanced)
- [TweetDeck](https://tweetdeck.twitter.com)
- [Mobile](https://mobile.twitter.com/search-advanced)

It is **not fully compatible** with:
- Twitter API v1.1
- Twitter API v2 (standard or premium search)

---

## 🚀 Quick Examples

```bash
"elon musk" (tesla OR spacex) -filter:retweets since:2022-01-01 lang:en
"openai" (source:tweetdeck OR source:twitter_web_app) filter:images min_faves:1000
from:NASA (filter:media -filter:images) until:2023-01-01
url:twitter.com/i/events/ -from:twittermoments
```

---

## ✅ How Matching Works

- **Tokens**: Twitter uses custom tokenization — punctuation (like hyphens) is normalized. `"state-of-the-art"` ≈ `"state of the art"`.
- **Fields matched**: username, @handle, tweet text, URLs (short + expanded).
- **Defaults**: Searches return “Top” tweets (with some engagement). Add `f=live` in URL or switch to “Latest” for all tweets.
- **Private/locked/suspended tweets** will not appear.
- **Spelling correction & plural forms** often apply unless `+word` or `"exact phrase"` is used.
- **Some operators require pairing with another for results to appear.**

---

## 🧠 Boolean Operators

- **Spaces** → Logical AND
- `OR` → Must be **uppercase**
- Parentheses `()` → Group logic
- `-` → Negation, works with most filters

```bash
(dog OR cat) (cute OR funny) -filter:retweets min_faves:50
```

---

## 🧰 Operator Categories

Click the section titles below to jump:

- [Tweet Content](#tweet-content)
- [Users](#users)
- [Geo](#geo)
- [Time](#time)
- [Tweet Type](#tweet-type)
- [Engagement](#engagement)
- [Media](#media)
- [More Filters](#more-filters)
- [App Specific](#app-specific)
- [Building Queries](#building-queries)
- [Limitations](#limitations)
- [Snowflake IDs](#snowflake-ids)
- [Quote Tweets](#quote-tweets)
- [Supported Languages](#supported-languages)
- [TweetDeck Equivalents](#tweetdeck-equivalents)

---

## 📚 Tweet Content

| Example | Description |
|--------|-------------|
| `nasa esa` | Matches tweets with both words |
| `nasa OR esa` | Matches either |
| `"state of the art"` | Exact phrase match |
| `+radiooooo` | Disables spelling correction |
| `-love` | Exclude word |
| `#tgif` | Hashtag |
| `$TSLA` | Cashtag |
| `url:youtube.com` | Matches tweets linking to YouTube |
| `lang:en` | Language (see [Languages](#supported-languages)) |

---

## 👤 Users

| Operator | Usage |
|---------|-------|
| `from:elonmusk` | Tweets sent by user |
| `to:elonmusk` | Tweets replying to user |
| `@elonmusk` | Mentions user |
| `list:username/list-name` | Tweets from public list |
| `filter:verified` / `filter:blue_verified` | Verified / Twitter Blue users |

---

## 📍 Geo

| Operator | Usage |
|---------|-------|
| `near:"San Francisco"` | Tweets geotagged nearby |
| `within:10km` | Add radius limit |
| `geocode:lat,long,radius` | More accurate than `near:` |
| `place:ID` | Use [Twitter place IDs](https://developer.twitter.com/en/docs/tweets/data-dictionary/overview/geo-objects.html#place) |

---

## ⏱️ Time

| Operator | Usage |
|---------|-------|
| `since:2023-01-01` | From this date (inclusive) |
| `until:2023-02-01` | Until this date (exclusive) |
| `since_time:` / `until_time:` | Unix timestamp in seconds |
| `within_time:3h` | Last N hours/days/minutes |

---

## 🧵 Tweet Type

| Operator | Usage |
|---------|-------|
| `filter:nativeretweets` | Retweets using RT button |
| `include:nativeretweets` | Show RTs with other tweets |
| `filter:quote` | Quote tweets |
| `conversation_id:TWEET_ID` | All tweets in thread |
| `filter:self_threads` | Only replies to own tweets |
| `card_name:` | Cards (e.g., `poll2choice_text_only`, `animated_gif`) |

---

## 🔥 Engagement

| Operator | Usage |
|---------|-------|
| `filter:has_engagement` | Any likes/RTs/replies |
| `min_retweets:100` | Minimum RTs |
| `min_faves:500` | Minimum likes |
| `-min_replies:10` | Maximum replies |

---

## 🎥 Media

| Operator | Usage |
|---------|-------|
| `filter:media` | Any media |
| `filter:images` | Only images |
| `filter:videos` | Only videos |
| `filter:twimg` | Native Twitter images |
| `filter:spaces` | Twitter Spaces |

---

## 🔎 More Filters

| Operator | Usage |
|---------|-------|
| `filter:links` | Has any link |
| `filter:mentions` | Contains @mention |
| `filter:hashtags` | Has hashtag |
| `filter:safe` | Excludes NSFW content |
| `filter:news` | Links to known news sources ([see full list](#news-sites)) |

---

## 📱 App Specific

| Operator | Example |
|---------|---------|
| `source:tweetdeck` | From TweetDeck |
| `source:"Twitter for iPhone"` | Use underscore if quoting fails: `Twitter_for_iPhone` |
| `card_url:` / `card_domain:` | Filter by embedded media |

See [Clients List](#common-clients) for full names.

---

## 🏗️ Building Queries

Examples:

```bash
(dog OR puppy) -filter:retweets min_faves:100 lang:en
from:nasa filter:media -filter:images
(space OR mars) since:2022-01-01 until:2022-06-01 filter:videos
"climate change" url:nytimes.com
```

Avoid:
- Hyphens or spaces in `source:` or `url:` — use underscores `_`
- Too many filters (limit is ~22–23 operators)

---

## ❄️ Snowflake IDs

To convert tweet time → ID (and vice versa):

```python
def convert_milliepoch_to_tweet_id(milliepoch):
    if milliepoch <= 1288834974657:
        raise ValueError("Date is too early (before snowflake implementation)")
    return (milliepoch - 1288834974657) << 22
```

- Start of snowflake epoch: `1288834974657` (UTC)
- Use `since_id:` or `max_id:` for precise time control

---

## 💬 Quote Tweets

- To find tweets quoting a **specific tweet**:
  ```bash
  url:twitter.com/elonmusk/status/1234567890123456789
  ```
- To find **any quotes** from a user:
  ```bash
  url:twitter.com/elonmusk/status/ -from:elonmusk
  ```

Remove `?s=20` or `?s=09` from shared URLs.

---

## 🌍 Supported Languages

Use ISO 639-1 codes like:

```bash
lang:en
lang:ja
lang:es
lang:ar
```

Special codes:
- `lang:und` → Undefined
- `lang:qht` → Hashtag-only tweets
- `lang:qme` → Media-only tweets
- Full [Language List Here](#supported-languages)

---

## 🛠️ Limitations

- Most `card_name:` searches only return tweets from the **last 7–8 days**
- Many operators only function **combined with others**
- APIs have separate indices and **do not respect these filters**

---

## 🧪 How This Was Compiled

This guide combines:
- Twitter Help and TweetDeck Docs
- @lucahammer, @eevee, @igorbrigadir’s work
- GitHub, Pastebin, Share URLs
- Trial, error, and undocumented experimentation

---

## 🧠 Known Unknowns

- `filter:news` likely uses a whitelist of domains (see [News Sites](#news-sites))
- Retweets behave inconsistently with engagement filters
- Some operators (`source:`, `lang:`) return inconsistent results

---

## 🧰 TweetDeck Search Equivalents

| TweetDeck Option | Equivalent Search |
|------------------|-------------------|
| "Images"         | `filter:images` |
| "Videos"         | `filter:videos` |
| "GIFs"           | `card_name:animated_gif` |
| "Broadcasts"     | `card_domain:pscp.tv OR card_domain:periscope.tv` |
| "Any Media"      | `(filter:images OR filter:videos)` |
| "Any Links"      | `filter:links` |

---

## 🧾 References & Credits

- [Twitter Search](https://twitter.com/search-advanced)
- [TweetDeck Help](https://help.twitter.com/en/using-twitter/advanced-tweetdeck-features)
- [Pushshift Docs](https://docs.google.com/document/d/1xVrPoNutyqTdQ04DXBEZW4ZW4A5RAQW2he7qIpTmG-M/)
- [Snowflake Epoch Calculator](https://www.epochconverter.com)