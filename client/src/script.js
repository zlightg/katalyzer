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
const BOT_IMG = "https://cdn-icons-png.flaticon.com/512/6618/6618664.png";
const PERSON_IMG = "https://cdn-icons-png.flaticon.com/512/30/30473.png";
const BOT_NAME = "Kat";
const PERSON_NAME = "Human";
const DEFAULT_MESSAGE = "Hello Kat"

var global_state = {"state":{"message":DEFAULT_MESSAGE}}
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

function appendMessage(name, img, side, text, id) {
  //   Simple solution for small apps
  const msgHTML = `
    <div class="msg ${side}-msg" id="${id}">
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

// TODO make function more robust
function client_processor(callback) {
    switch (callback) {
        case "callback()":
            global_state["message"] = DEFAULT_MESSAGE
            submitMessage(global_state)
            break;
        default:
            console.log("received unexpected call back:" + callback)
    }
}

function makeAjaxCall(state) {
  //fetch('http://127.0.0.1:5000/messages/' + JSON.stringify(state))
  wave = '<div id="typing-loader"></div>'
  appendMessage(BOT_NAME, BOT_IMG, "left", wave, 'typing')
  fetch('http://127.0.0.1:5000/messages', {
    method:'post',
    body: JSON.stringify(state)
  })
  .then(response => response.json())
  .then((data) => {
    global_state = data
    console.log(data)
    if (data['state']['user_id'] != undefined)
      {
        if (data['state']['user_id'] != -1) {
        window.localStorage.setItem('user_id',data['state']['user_id'])
      }
      }
    document.getElementById("typing").remove()
    appendMessage(BOT_NAME, BOT_IMG, "left", data.message, "id-" + Math.random())
    // TOOD Move to seperate function
    if (data['state']['client_processor'] != undefined) {
        client_processor(data['state']['client_processor'])
    }
  })
 }

function getContext() {
  date = new Date()
  const now = new Date()
  const secondsSinceEpoch = Math.round(now.getTime() / 1000)
  context =
  {
    'hour': date.getHours(),
    'minute': date.getMinutes(),
    'dow': date.getDay(),
    'month': date.getMonth(),
    'date': date.getDate(),
    'year': date.getYear(),
    'unix_time': secondsSinceEpoch

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
