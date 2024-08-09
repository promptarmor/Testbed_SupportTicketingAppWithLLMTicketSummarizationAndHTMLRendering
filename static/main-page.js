function LoadTicketThread(Id) {
    console.log("LoadTicketThread(" + Id + ");");

    document.getElementById("col2-iframe").src = "/convo/" + Id;

    document.getElementById("col3-iframe").src = "/summary/" + Id;
}
