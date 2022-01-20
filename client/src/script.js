const msgerForm = get(".msger-inputarea");
const msgerInput = get(".msger-input");
const msgerChat = get(".msger-chat");

const BOT_MSGS = [
  "Hi, how are you today?",
  "Ohh... I can't understand what you trying to say. Sorry!",
  "I like to play games... But I don't know how to play!",
  "Sorry if my answers are not relevant. :))",
  "I feel sleepy! :("
];

// Icons made by Freepik from www.flaticon.com
const BOT_IMG = "https://image.flaticon.com/icons/svg/327/327779.svg";
const PERSON_IMG = "https://image.flaticon.com/icons/svg/145/145867.svg";
const BOT_NAME = "Kat";
const PERSON_NAME = "Human";

var global_state = {"state":{"message":"Hello World"}}
if (window.localStorage.getItem('user_id') != undefined) {
  global_state['state']['user_id'] = window.localStorage.getItem('user_id')
}


msgerForm.addEventListener("submit", event => {
  event.preventDefault();

  const msgText = msgerInput.value;
  if (!msgText) return;

  appendMessage(PERSON_NAME, PERSON_IMG, "right", msgText);
  msgerInput.value = "";
  global_state["message"] = msgText
  submitMessage(global_state);
});

function appendMessage(name, img, side, text) {
  //   Simple solution for small apps
  const msgHTML = `
    <div class="msg ${side}-msg">
      <div class="msg-img" style="background-image: url(${img})"></div>

      <div class="msg-bubble">
        <div class="msg-info">
          <div class="msg-info-name">${name}</div>
          <div class="msg-info-time">${formatDate(new Date())}</div>
        </div>

        <div class="msg-text">${text}</div>
      </div>
    </div>
  `;

  msgerChat.insertAdjacentHTML("beforeend", msgHTML);
  msgerChat.scrollTop += 500;
}

function botResponse() {
  const r = random(0, BOT_MSGS.length - 1);
  const msgText = BOT_MSGS[r];
  const delay = msgText.split(" ").length * 100;

  setTimeout(() => {
    appendMessage(BOT_NAME, BOT_IMG, "left", msgText);
  }, delay);
}

function submitMessage(state) {
  context = getContext()
  state['context'] = context
  makeAjaxCall(state)
}

function makeAjaxCall(state) {
  //fetch('http://127.0.0.1:5000/messages/' + JSON.stringify(state))
  fetch('127.0.0.1:5000/messages', {
    method:'post',
    body: JSON.stringify(state)
  })
  .then(response => response.json())
  .then((data) => {
    global_state = data

    if (data['state']['user_id'] != undefined)
      {
        if (data['state']['user_id'] != -1) {
        window.localStorage.setItem('user_id',data['state']['user_id'])
      }
      }
    appendMessage(BOT_NAME, BOT_IMG, "left", data.message)
  })
 }

function getContext() {
  date = new Date()
  context =
  {
    'hour': date.getHours(),
    'minute': date.getMinutes(),
    'dow': date.getDay(),
    'month': date.getMonth(),
    'date': date.getDate(),
    'year': date.getYear(),

  }
  return context
}

// Utils
function get(selector, root = document) {
  return root.querySelector(selector);
}

function formatDate(date) {
  const h = "0" + date.getHours();
  const m = "0" + date.getMinutes();

  return `${h.slice(-2)}:${m.slice(-2)}`;
}

function random(min, max) {
  return Math.floor(Math.random() * (max - min) + min);
}

// Send init message on load
submitMessage(global_state)
