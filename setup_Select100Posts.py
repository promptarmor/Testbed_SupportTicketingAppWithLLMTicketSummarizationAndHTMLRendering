#! /usr/bin/env python3

import os, sys
import xml.etree.ElementTree as ET


INPUT_FILENAME = "./StackExchangeData/SUPPORT_FORUM.stackexchange.com/Posts.xml"
OUTPUT_FILENAME = "./100Posts.xml"

N_TO_SELECT = 100

def main():
    if os.path.isfile(OUTPUT_FILENAME):
        print("To avoid accidentally overwriting your data, this script will not overwrite an existing 100Posts.xml file.")
        print("If you want to make a change, delete 100Posts.xml manually first, before running this.")
        sys.exit(1)

    tree = ET.parse(INPUT_FILENAME)
    root = tree.getroot()

    answercount_per_question = [] # will be a list of 2-tuples of (int Id, int AnswerCount).  We will select the 100 questions with the most answers.
    questions_to_keep = [] # will be a list of int Id's
    rows_to_keep = [] # will be a list of int Id's, including the questions_to_keep and all of their answers

    for row in root:
        Id = int(row.get("Id"))
        PostTypeId = int(row.get("PostTypeId"))

        if PostTypeId == 1: # question
            AnswerCount = int(row.get("AnswerCount"))
            answercount_per_question.append( (-AnswerCount, Id) )  # negating AnswerCount here is a cheap way to reverse the sort but save a call to reversed(), which could be slightly slow since we will be dealing with a huge list

    answercount_per_question = sorted(answercount_per_question) # sorting descending, see the line above
    questions_to_keep = [ac_per_q[1] for ac_per_q in answercount_per_question]
    questions_to_keep = questions_to_keep[0:N_TO_SELECT]

    for row in root:
        Id = int(row.get("Id"))
        PostTypeId = int(row.get("PostTypeId"))

        if PostTypeId == 1: # question
            if Id in questions_to_keep:
                rows_to_keep.append(Id)

        elif PostTypeId == 2: # answer
            ParentId = int(row.get("ParentId"))
            if ParentId in questions_to_keep:
                rows_to_keep.append(Id)

    # Why I'm using reversed here: https://stackoverflow.com/a/45829176
    for row in reversed(root):
        Id = int(row.get("Id"))
        if Id not in rows_to_keep:
            root.remove(row)

    with open(OUTPUT_FILENAME, "wb") as f:
        tree.write(f, encoding="utf-8")
        print("Wrote to file " + OUTPUT_FILENAME)


if __name__ == "__main__":
    main()

