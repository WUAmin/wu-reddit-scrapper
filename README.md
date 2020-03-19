# wu-reddit-scrapper
Scrape images and videos from [Reddit](https://www.reddit.com/) using [PRAW (Python Reddit API Wrapper)](https://github.com/praw-dev/praw) and [youtube-dl](https://github.com/ytdl-org/youtube-dl/).
Script will look at config file, get list of subreddits from `repo` and download new submissions. After each media download.


## Configuration
1. Create a Reddit account and go to [Reddit's apps page](https://www.reddit.com/prefs/apps). Click "are you a developer? create an app..." and create a "Personal use script".
2. Make a copy from `config.json.sample` and edit `id` (Personal use script), `secret` and `name` according to your Reddit API information.
3. Inside `repo` in config file.

You can use `-c /path/to/config.json` to run script using different configuration file.
####Config sample:
```json
{
    "version": "1.1",
    "download_path": "Downloads",
    "reddit": {
        "id": "YOUR-REDDIT-PERSONAL-USE-SCRIPT",
        "secret": "YOUR-REDDIT-API-SECRET",
        "name": "YOUR-REDDIT-API-NAME",
        "repo": [
            {
                "subreddit": "pics",
                "dirname": null,
                "limit_requests": 50,
                "last_update": 1584661281.0
            },
            {
                "subreddit": "gif",
                "dirname": "animated",
                "limit_requests": 10,
                "last_update": 1584660564.0
            }
        ]
    }
}
```
|Key             | Description     |
|----------------|-----------------|
|`version`       | on every script update, version will change. and script will notice you to recheck your configuration with `config.json.sample` and update it. to make sure config match the script. |
|`download_path` | path to download directory for media files. |
|`id`            | "Personal use script" key in your Reddit account [apps page](https://www.reddit.com/prefs/apps)  |
|`secret`        | "secret" key in your Reddit account [apps page](https://www.reddit.com/prefs/apps)  |
|`name`          | "name" of your API in your Reddit account [apps page](https://www.reddit.com/prefs/apps)  |
|`subreddit`     | name of subreddit. for example "pics" for https://www.reddit.com/r/pics/|
|`direname`      | "null" if you want files go to root of `download_path`. you can specify a directory name inside `download_path`. like "animated" in example |
|`limit_requests`| number of submissions to get for this subreddit. |
|`last_update`| Script will update it automatically. store the last submission downloaded from this subreddit for avoiding duplicate media file |

