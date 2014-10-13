"""Console-level entry point."""
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
from core import follow_publication, delete_front_page, analyze_process
from core import init_db, see_words_for, boot_sql_alchemy
from config import ConfigException

def set_up(args):
    if not os.path.exists("corpus"):
        os.mkdir("corpus")
    return init_db()

def delete_fp(args):
    return delete_front_page(args.id)   

def read_all(args):
    return analyze_process()

def view_words(args):
    return see_words_for(args.publication_name, args.proper, args.limit)

def add_publication(args):
    return follow_publication(args.name, args.url)

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    follow = subparsers.add_parser("follow", help="follow help")
    follow.add_argument("name", help="Name of the publication to follow.")
    follow.add_argument("url",
                        help="URL of the front page for this publication.")
    words = subparsers.add_parser("words",
                                  help="Find words used by a publication")
    words.add_argument("publication_name",
                       help="Name of the publication")
    words.add_argument("limit",
                       help="Max number of words", type=int)
    words.add_argument("--proper",
                       help="Proper nouns or commons ones", action="store_true")

    delete = subparsers.add_parser("delete",
                                   help="delete help")
    delete.add_argument("id", type=int,
                        help="Id of the front page to delete")

    init = subparsers.add_parser("init", help="Setup database.")
    read = subparsers.add_parser("read",
                                 help="Read and analyze followed frontpages.")
    follow.set_defaults(func=add_publication)
    words.set_defaults(func=view_words)
    init.set_defaults(func=set_up)
    read.set_defaults(func=read_all)
    delete.set_defaults(func=delete_fp)
    args = parser.parse_args()

    if hasattr(args, "func"):
        try:
            boot_sql_alchemy()
            res = args.func(args)
            print(res)
        except ConfigException as config_failure:
            print("[FAILED] - Your configuration file is faulty.")
            print(config_failure)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
