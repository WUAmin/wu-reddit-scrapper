import argparse
import datetime
import json
import os
import re
from urllib.error import HTTPError

import praw
import youtube_dl
from prawcore.exceptions import Redirect
from prawcore.exceptions import ResponseException


class App:
    config: dict = None


def load_config(filepath: str):
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data
    except Exception as e:
        print("❌ Error on loading config: {}".format(str(e)))
        return None


def save_config(filepath: str, config: dict):
    try:
        with open(filepath, 'w') as f:
            f.write(json.dumps(config, indent=2, sort_keys=False))
    except Exception as e:
        print("❌ Error on saving config: {}".format(str(e)))
        return None
    return True


def _download_media_hook(d):
    if d['status'] == 'finished':
        print('Done')


def download_media(submission, dir_to_save: str):
    try:
        # Prepare filename
        filepath: str = '{:.0f}_{}'.format(submission.created,
                                           re.sub(r"[^a-zA-Z\ 0-9\-\_\+\=\.\,\[\]\(\)]", "", submission.title))
        filepath = os.path.join(dir_to_save, filepath[:250])

        # Download using youtube-dl
        ydl_opts = {
            'outtmpl': '{}.%(ext)s'.format(filepath),
            'progress_hooks': [_download_media_hook],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([submission.url])
    except Exception as e:
        print("❌ Error downloading reddit submission using youtube-dl: {}".format(str(e)))


def get_reddit_submissions(repo, limit=50) -> list:
    try:
        r = praw.Reddit(client_id=App.config['reddit']['id'], client_secret=App.config['reddit']['secret'],
                        user_agent=App.config['reddit']['name'])
        submissions = r.subreddit(repo['name']).new(limit=limit)
        return list(submissions)
    except Redirect:
        print("❌ Invalid Subreddit!")
    except HTTPError:
        print("❌ Too many Requests. Try again later!")
    except ResponseException:
        print("❌ Client info is wrong. Check again.")
    except Exception as e:
        print("❌ Error get reddit submissions: {}".format(str(e)))
    return None


def setup_download_path(dirpath: str):
    if os.path.exists(dirpath):
        if not os.path.isdir(dirpath):
            print("❌ Error `{}` is not a  directory.".format(dirpath))
            exit(1)
            # remove all incomplete files (temps)
            files = os.listdir(dirpath)
            for f in files:
                if f.endswith(".part") or f.endswith(".ytdl"):
                    try:
                        os.remove(os.path.join(dirpath, f))
                    except Exception as e:
                        print("❌ Error can not remove temp file `{}`: {}".format(dirpath, f, str(e)))
    else:
        os.mkdir(dirpath)
        print("✅ Create `{}` directory.".format(dirpath))


def parse_arg():
    parser = argparse.ArgumentParser(description='Scrape reddit')
    parser.add_argument('-c', '--config', default="config.json",
                        help='Path to json configuration file)')
    args = parser.parse_args()
    return args.config


def main():
    # Load config file
    config_filepath = parse_arg()
    App.config = load_config(config_filepath)

    # Check/Create Download path
    setup_download_path(App.config['download_path'])

    for repo in App.config['reddit']['repo']:
        dl_dirpath = App.config['download_path']
        # Check/Create repo directory on Dwnloadpath
        if repo['dirname']:
            dl_dirpath = os.path.join(dl_dirpath, repo['dirname'])
            setup_download_path(dl_dirpath)

        limit = 50
        if repo['limit_requests']:
            limit = repo['limit_requests']

        submissions = get_reddit_submissions(repo=repo, limit=limit)
        for submission in reversed(submissions):
            print("\nDate:  {}"
                  "\nTitle: {}"
                  "\nURL:   {}"
                  .format(datetime.datetime.fromtimestamp(submission.created), submission.title, submission.url))

            if repo['last_update']:
                if submission.created <= repo['last_update']:
                    print("⏭️ Skipped (Downloaded before)")
                    continue

            download_media(submission=submission, dir_to_save=dl_dirpath)
            repo['last_update'] = submission.created
            save_config(config_filepath, App.config)


if __name__ == '__main__':
    main()
