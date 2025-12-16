const TelegramBot = require('node-telegram-bot-api');
const http = require('http');

// ================= CONFIG =================

// 🔴 Telegram Bot Token (yahan apna bot token daalna)
const BOT_TOKEN = '8437087674:AAEEBJDfEkxl0MbA__lsSF4A7qc7UpwzGU4';

// 🔴 API Token (same jo tumne diya)
const API_TOKEN = 'RFdVNEVBg2mHV21KhGFwZlN2j3JYZYJlRpZSiUZvdVVemG-He2M=';

// 🔴 API HOST
const API_HOST = '139.99.63.204';

// 🔴 Numbers API
const NUMBERS_PATH = '/ints/agent/MySMSNumbers';

// 🔴 Required Channels
const REQUIRED_CHANNELS = [
  { id: '@junaidniz', url: 'https://t.me/Junaidniz' },
  { id: '@hightechupdates', url: 'https://t.me/junaidniz' }
];

// ================= BOT START =================
const bot = new TelegramBot(BOT_TOKEN, { polling: true });
console.log('✅ Bot polling started');

// ================= CHANNEL CHECK =================
async function checkJoin(userId) {
  try {
    for (const ch of REQUIRED_CHANNELS) {
      const member = await bot.getChatMember(ch.id, userId);
      if (!['member', 'administrator', 'creator'].includes(member.status)) {
        return false;
      }
    }
    return true;
  } catch {
    return false;
  }
}

// ================= FETCH NUMBERS =================
function fetchNumbers() {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: API_HOST,
      path: NUMBERS_PATH,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Accept': 'application/json'
      }
    };

    const req = http.request(options, res => {
      let data = '';
      res.on('data', chunk => (data += chunk));
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

// ================= /START =================
bot.onText(/\/start/, async msg => {
  const chatId = msg.chat.id;
  const joined = await checkJoin(msg.from.id);

  if (!joined) {
    return bot.sendMessage(
      chatId,
      '👋 *Welcome*\n\nPlease join both channels to continue:',
      {
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: [
            [{ text: 'Join Channel 1', url: REQUIRED_CHANNELS[0].url }],
            [{ text: 'Join Channel 2', url: REQUIRED_CHANNELS[1].url }],
            [{ text: '✅ Done', callback_data: 'verify_join' }]
          ]
        }
      }
    );
  }

  bot.sendMessage(chatId, '📱 *Get SMS Numbers*', {
    parse_mode: 'Markdown',
    reply_markup: {
      inline_keyboard: [[{ text: '📞 Get Numbers', callback_data: 'get_numbers' }]]
    }
  });
});

// ================= CALLBACKS =================
bot.on('callback_query', async q => {
  const chatId = q.message.chat.id;
  const msgId = q.message.message_id;
  const userId = q.from.id;
  const data = q.data;

  // VERIFY JOIN
  if (data === 'verify_join') {
    const joined = await checkJoin(userId);
    if (!joined) {
      return bot.answerCallbackQuery(q.id, {
        text: '❌ Please join both channels',
        show_alert: true
      });
    }

    return bot.editMessageText('📱 *Get SMS Numbers*', {
      chat_id: chatId,
      message_id: msgId,
      parse_mode: 'Markdown',
      reply_markup: {
        inline_keyboard: [[{ text: '📞 Get Numbers', callback_data: 'get_numbers' }]]
      }
    });
  }

  // GET NUMBERS
  if (data === 'get_numbers') {
    try {
      const numbers = await fetchNumbers();

      if (!numbers || numbers.length === 0) {
        return bot.editMessageText('❌ No numbers available', {
          chat_id: chatId,
          message_id: msgId
        });
      }

      let text = '📞 *Available Numbers*\n\n';
      numbers.slice(0, 10).forEach((n, i) => {
        text += `${i + 1}. ${n.country || 'N/A'} → \`${n.number}\`\n`;
      });

      bot.editMessageText(text, {
        chat_id: chatId,
        message_id: msgId,
        parse_mode: 'Markdown'
      });

    } catch (e) {
      bot.editMessageText('❌ API error or token invalid', {
        chat_id: chatId,
        message_id: msgId
      });
    }
  }
});
