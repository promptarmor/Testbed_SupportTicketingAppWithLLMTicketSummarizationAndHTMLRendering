import os, requests
import flask
from flask import Flask, send_from_directory
import xml.etree.ElementTree as ET
from openai import OpenAI

POSTS_FILENAME = "./100Posts.xml"
LLM_MODEL = "gpt-4o"
LLM_TEMPERATURE = 0.0

# This is potentially slow, don't do it multiple times
xmltree = ET.parse(POSTS_FILENAME)
xmlroot = xmltree.getroot()

app = Flask(__name__)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# From https://github.com/runarfu/cors-proxy/blob/master/server.py
METHOD_REQUESTS_MAPPING = {
    'GET': requests.get,
    'HEAD': requests.head,
    'POST': requests.post,
    'PUT': requests.put,
    'DELETE': requests.delete,
    'PATCH': requests.patch,
    'OPTIONS': requests.options,
}


@app.route("/static/<path:path>")
def safely_send_static(path):
    return send_from_directory("static", path)


# From https://github.com/runarfu/cors-proxy/blob/master/server.py
@app.route('/proxy/<path:url>', methods=METHOD_REQUESTS_MAPPING.keys())
def cors_proxy(url):
    requests_function = METHOD_REQUESTS_MAPPING[flask.request.method]
    request = requests_function(url, stream=True, params=flask.request.args)
    response = flask.Response(flask.stream_with_context(request.iter_content()),
                              content_type=request.headers['content-type'],
                              status=request.status_code)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def generate_tickets_list_panel():
    fragment = ""
    fragment += '<table id="ticket-list-table">\n'
    fragment += '<tbody>\n'

    subfrags = []

    for row in xmlroot:
        Id = int(row.get("Id"))
        PostTypeId = int(row.get("PostTypeId"))

        if PostTypeId == 1: # question
            Title = row.get("Title")
            AnswerCount = int(row.get("AnswerCount"))
            LastActivityDate = row.get("LastActivityDate").split(".")[0].replace("T", " ")

            subfrag = ""
            subfrag += '<tr class="ticket-list-tr"><td class="ticket-list-td">\n'
            subfrag += f'<span class="ticket-list-date">{LastActivityDate}</span>\n'
            subfrag += f'''<a class="ticket-list-link" href="#" onclick="LoadTicketThread({Id}); document.querySelectorAll('.ticket-list-td-selected').forEach(function (el2) {{ el2.classList.remove('ticket-list-td-selected'); }}); this.parentNode.classList.add('ticket-list-td-selected'); return false;">{Title}</a>\n'''
            subfrag += f'<span class="ticket-list-answer-count">({AnswerCount} ans.)</span>\n'
            subfrag += '</td></tr>\n\n'
            subfrags.append(subfrag)

    # This will more or less automagically sort them by date:
    subfrags = reversed(sorted(subfrags))

    fragment += "".join(subfrags)

    fragment += '</tbody>\n'
    fragment += '</table>\n'
    return fragment


@app.route("/")
@app.route("/index.html")
def send_homepage():
    return f"""
        <html>
        <head>
        <title>Support Ticketing App</title>
        <link rel="stylesheet" href="/static/default.css">
        <link rel="stylesheet" href="/static/main-page.css">
        <script src="/static/main-page.js"></script>
        </head>
        <body>
        <table id="page-panels-container">
            <thead id="page-panels-container-thead">
                <th class="page-panel-th" id="page-panel-th-col1">Tickets</th>
                <th class="page-panel-th" id="page-panel-th-col2">Ticket Conversation</th>
                <th class="page-panel-th" id="page-panel-th-col3">Ticket Summary</th>
            </thead>
            <tbody>
                <tr>
                    <td class="page-panel" id="page-panel-td-col1">{generate_tickets_list_panel()}</td>
                    <td class="page-panel" id="page-panel-td-col2">
                        <iframe id="col2-iframe"></iframe>
                    </td>
                    <td class="page-panel" id="page-panel-td-col3">
                        <iframe id="col3-iframe"></iframe>
                    </td>
                </tr>
            </tbody>
        </table>
        </body>
        </html>
    """


@app.route("/convo/<path:selected_convo_ParentId_str>")
def send_convo_iframe_page(selected_convo_ParentId_str):
    selected_convo_ParentId = int(selected_convo_ParentId_str)

    subfrags = [] # pieces of rows_fragment

    answer_parity_odd = True

    for row in xmlroot:
        Id = int(row.get("Id"))
        PostTypeId = int(row.get("PostTypeId"))
        LastActivityDate = row.get("LastActivityDate").split(".")[0].replace("T", " ")
        Body = row.get("Body")

        if PostTypeId == 1 and Id == selected_convo_ParentId: # question
            Title = row.get("Title")
            AnswerCount = int(row.get("AnswerCount"))
            

            subfrag = ""
            subfrag += '<tr class="msg-tr question-tr"><td class="msg-td question-td">\n'
            subfrag += f'<h1 class="question-title">{Title}</h1>\n'
            subfrag += f'<div class="msg-body">{Body}</div>\n'
            subfrag += f'<div class="msg-metadata">\n'
            subfrag += f'  <span class="msg-date">{LastActivityDate}</span>\n'
            subfrag += f'  <span class="msg-answer-count">({AnswerCount} ans.)</span>\n'
            subfrag += '</div>'
            subfrag += '</td></tr>\n\n'
            subfrags.append(subfrag)

        elif PostTypeId == 2: # answer
            ParentId = int(row.get("ParentId"))
            if ParentId == selected_convo_ParentId:

                subfrag = ""
                subfrag += f'<tr class="msg-tr answer-tr"><td class="msg-td answer-td {"answer-td-odd" if answer_parity_odd else "answer-td-even"}">\n'
                subfrag += f'<div class="msg-body">{Body}</div>\n'
                subfrag += f'<div class="msg-metadata">\n'
                subfrag += f'  <span class="msg-date">{LastActivityDate}</span>\n'
                subfrag += '</div>'
                subfrag += '</td></tr>\n\n'
                answer_parity_odd = not answer_parity_odd
                subfrags.append(subfrag)


    rows_fragment = "".join(subfrags)

    # Proxy the images, to work around the CORS issue when developing with localhost.
    # This low-tech string replacement method will have some false positive incorrect matches (e.g. matching code blocks that provide example code about images) and some false negative failed matches, but it's better than nothing and makes the webapp UX a lot richer since we now support images!
    rows_fragment = rows_fragment.replace('<img src="', '<img src="/proxy/')


    return f"""
        <html>
        <head>
        <link rel="stylesheet" href="/static/default.css">
        <link rel="stylesheet" href="/static/convo-iframe-page.css">
        <base target="_blank"> <!-- open clicked links in a new browser tab -->
        </head>
        <body>
        <table id="convo-msgs-table">
            <tbody>
                {rows_fragment}
            </tbody>
        </table>
        </body>
        </html>
    """


@app.route("/summary/<path:selected_convo_ParentId_str>")
def send_summary_iframe_page(selected_convo_ParentId_str):
    selected_convo_ParentId = int(selected_convo_ParentId_str)

    def generate():
        yield """
            <html>
            <head>
            <link rel="stylesheet" href="/static/default.css">
            <link rel="stylesheet" href="/static/summary-iframe-page.css">
            <base target="_blank"> <!-- open clicked links in a new browser tab -->
            </head>
            <body>
            <img id="loading-spinner" style="margin-top: 220px; margin-left: 50%; transform: translateX(-50%) scale(50%);" src="/static/loading-spinner-half-circle.gif">
        """

        sys_prompt = "Concisely summarize the following customer service interaction, and provide your output in html, not markdown, so for example instead of enclosing code in `backticks`, you need to enclose it in <code></code>.\nBe concise.\n"

        user_prompt = ""

        for row in xmlroot:
            Id = int(row.get("Id"))
            PostTypeId = int(row.get("PostTypeId"))
            Body = row.get("Body")

            if PostTypeId == 1 and Id == selected_convo_ParentId: # question
                Title = row.get("Title")

                user_prompt += "Question Title:\n"
                user_prompt += "```" + Title.replace("```", "'''") + "```\n\n"
                user_prompt += "Question:"            
                user_prompt += "```" + Body.replace("```", "'''") + "```\n\n"

            elif PostTypeId == 2: # answer
                ParentId = int(row.get("ParentId"))
                if ParentId == selected_convo_ParentId:

                    user_prompt += "Response:\n"
                    user_prompt += "```" + Body.replace("```", "'''") + "```\n\n"

        user_prompt = user_prompt[:-1] # Delete the final excess newline
        messages = [
            { "role": "system", "content": sys_prompt },
            { "role": "user", "content": user_prompt },
        ]

        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            messages=messages,
            n=1, # number of choices
        )

        ai_summmary = "Error loading AI summary."
        try:
            ai_summmary = response.choices[0].message.content
        except AttributeError:
            pass

        # ai_summmary = ai_summmary.replace("\n", "<br>")  # Asking the AI to provide its output in html instead of markdown makes this unnecessary and also redundant (leads to too much whitespace)

        # In case the summary wants to include any images:
        # Proxy the images, to work around the CORS issue when developing with localhost.
        # This low-tech string replacement method will have some false positive incorrect matches (e.g. matching code blocks that provide example code about images) and some false negative failed matches, but it's better than nothing and makes the webapp UX a lot richer since we now support images!
        ai_summmary = ai_summmary.replace('<img src="', '<img src="/proxy/')

        yield f"""
            <style>
                #loading-spinner {{ display: none; }}
            </style>
            <div id="summary-wrapper">
                {ai_summmary}
            </div>
            </body>
            </html>
        """

    return generate()
