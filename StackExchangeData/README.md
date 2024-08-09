# Instructions to acquire source ticket data

From https://archive.org/download/stackexchange :
Download vi.stackexchange.com.7z
(or whichever forum's archive you prefer - vi was chosen for being basically a support forum about a specific "product")

Extract the archive.

Rename the extracted folder (e.g. "salesforce.stackexchange.com" or "vi.stackexchange.com") to "SUPPORT_FORUM.stackexchange.com"

# How to verify that your directory structure is correct

`brew install tree`

`tree`

The results should look like this:
`(venv) jon@Jonathans-Laptop StackExchange % tree
.
├── README.md
└── SUPPORT_FORUM.stackexchange.com
    ├── Badges.xml
    ├── Comments.xml
    ├── PostHistory.xml
    ├── PostLinks.xml
    ├── Posts.xml
    ├── Tags.xml
    ├── Users.xml
    └── Votes.xml`
