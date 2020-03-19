import argparse
import datetime
import json
import os
import re
import shutil
import urllib.request
from urllib.error import HTTPError

import praw
import youtube_dl
from prawcore.exceptions import Redirect
from prawcore.exceptions import ResponseException


class App:
    version = "1.3"
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
        NORMAL_DL_EXT = [".jpg", ".jpeg", ".png", ".gif", ".gifv"]
        filename, ext = os.path.splitext(submission.url)
        if ext.lower() in NORMAL_DL_EXT:
            filepath = os.path.split(submission.url)[1]
            filepath = '{:.0f}_{}'.format(submission.created, filepath)
            filepath = os.path.join(dir_to_save, filepath)
            # Download the file from `url` and save it locally under `file_name`:
            with urllib.request.urlopen(submission.url) as response, open(filepath, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        else:
            # Download using youtube-dl
            # with youtube_dl.YoutubeDL({}) as ydl:
            #     result = ydl.extract_info(submission.url, download=False)
            #     filepath = ydl.prepare_filename(result)
            #     filepath = '{:.0f}_{}'.format(submission.created, filepath)
            #     filepath = os.path.join(dir_to_save, filepath)

            # # Prepare filename
            filepath: str = '{:.0f}_{}'.format(submission.created,
                                               re.sub(r"[^a-zA-Z\ 0-9\-\_\+\=\.\,\[\]\(\)]", "", submission.title))
            filepath = os.path.join(dir_to_save, filepath[:200])

            ydl_opts = {
                # 'outtmpl': '{}.%(ext)s'.format(filepath),
                'outtmpl': filepath,
                'progress_hooks': [_download_media_hook],
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl2:
                ydl2.download([submission.url])
                # result = ydl.extract_info(submission.url, download=False)
                # filepath = ydl.prepare_filename(result)
    except Exception as e:
        print("❌ Error downloading reddit submission using youtube-dl: {}".format(str(e)))
        return None
    return filepath


def get_reddit_submissions(repo, limit=50) -> list:
    try:
        r = praw.Reddit(client_id=App.config['reddit']['id'], client_secret=App.config['reddit']['secret'],
                        user_agent=App.config['reddit']['name'])
        submissions = r.subreddit(repo['subreddit']).new(limit=limit)
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
        try:
            os.mkdir(dirpath)
            print("✅ Create `{}` directory.".format(dirpath))
        except Exception as e:
            print("❌ Error can not create directory `{}`: {}".format(dirpath, str(e)))


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

    # Check if version of script match version of config
    if App.version != App.config['version']:
        print("\n⚠️️ Script version is `{}` but config version is `{}`."
              " check your configuration with script sample again,"
              " and update configuration version to match the script version.\nScript Version: {}\n"
              .format(App.version, App.config['version'], App.version))
        exit(1)

    # Check/Create Download path
    setup_download_path(App.config['download_path'])

    for repo in App.config['reddit']['repo']:
        dl_dirpath = App.config['download_path']
        # Check/Create repo directory on Download path
        if 'dirname' in repo:
            if repo['dirname']:
                dl_dirpath = os.path.join(dl_dirpath, repo['dirname'])
                setup_download_path(dl_dirpath)
        if 'copy_to' in repo:
            if isinstance(repo['copy_to'], list):
                for copy_to in repo['copy_to']:
                    setup_download_path(os.path.join(App.config['download_path'], copy_to))

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

            file_path = download_media(submission=submission, dir_to_save=dl_dirpath)
            if 'copy_to' in repo:
                if isinstance(repo['copy_to'], list):
                    if file_path:
                        for copy_to in repo['copy_to']:
                            try:
                                shutil.copy2(file_path, os.path.join(App.config['download_path'], copy_to))
                            except Exception as e:
                                print("❌ Error can copy `{}` to copy_to of `{}`: {}".format(file_path, copy_to, str(e)))
            repo['last_update'] = submission.created
            save_config(config_filepath, App.config)


if __name__ == '__main__':
    main()
