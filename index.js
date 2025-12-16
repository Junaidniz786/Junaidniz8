require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const https = require('https');

// ================= CONFIG =================
const TOKEN = 8437087674:AAEEBJDfEkxl0MbA__lsSF4A7qc7UpwzGU4;
const bot = new TelegramBot(TOKEN, { polling: true });

// OTP GROUP ID (BOT MUST BE ADMIN)
const OTP_GROUP_ID = -1003361941052; // 🔴 change this

// REQUIRED CHANNELS
const REQUIRED_CHANNELS = [
  { id: '@junaidniz', name: 'Channel 1' },
  { id: '@junaidniz', name: 'Channel 2' }
];

// USER → NUMBER MAP
const numberUserMap = new Map();
// DUPLICATE OTP FILTER
const seenOtps = new Set();

console.log('✅ Bot polling started...');

// ================= API FUNCTIONS =================
function fetchNumbersAPI() {
  return new Promise((resolve, reject) => {
    https.get(
      'https://www.junaidniz.pw/api/tempotps?type=numbers',
      res => {
        let data = '';
        res.on('data', d => data += d);
        res.on('end', () => {
          try { resolve(JSON.parse(data)); }
          catch (e) { reject(e); }
        });
      }
    ).on('error', reject);
  });
}

function fetchSMSAPI() {
  return new Promise((resolve, reject) => {
    https.get(
      'https://www.junaidniz.pw/api/tempotps?type=sms',
      res => {
        let data = '';
        res.on('data', d => data += d);
        res.on('end', () => {
          try { resolve(JSON.parse(data)); }
          catch (e) { reject(e); }
        });
      }
    ).on('error', reject);
  });
}

// ================= CHANNEL CHECK =================
async function checkJoin(userId) {
  try {
    for (const ch of REQUIRED_CHANNELS) {
      const m = await bot.getChatMember(ch.id, userId);
      if (!['member','administrator','creator'].includes(m.status)) {
        return false;
      }
    }
    return true;
  } catch {
    return false;
  }
}

// ================= /START =================
bot.onText(/\/start/, async (msg) => {
  const chatId = msg.chat.id;
  const joined = await checkJoin(msg.from.id);

  if (!joined) {
    bot.sendMessage(chatId,
      '👋 *Welcome to OTP KING*\n\nPlease join channels:',
      {
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: [
            [{ text: 'Join Channel 1', url: 'https://t.me/otpkingfreenumbers' }],
            [{ text: 'Join Channel 2', url: 'https://t.me/hightechupdates' }],
            [{ text: '✅ Done', callback_data: 'verify_join' }]
          ]
        }
      }
    );
    return;
  }

  bot.sendMessage(chatId, '🌍 *Select Country*', {
    parse_mode: 'Markdown',
    reply_markup: { inline_keyboard: [[{ text: '📱 Get Numbers', callback_data: 'get_numbers' }]] }
  });
});

// ================= CALLBACKS =================
bot.on('callback_query', async (q) => {
  const chatId = q.message.chat.id;
  const userId = q.from.id;
  const msgId = q.message.message_id;
  const data = q.data;

  // VERIFY JOIN
  if (data === 'verify_join') {
    const joined = await checkJoin(userId);
    if (!joined) {
      bot.answerCallbackQuery(q.id, { text: '❌ Join both channels', show_alert: true });
      return;
    }
    bot.editMessageText('🌍 *Select Country*', {
      chat_id: chatId,
      message_id: msgId,
      parse_mode: 'Markdown',
      reply_markup: { inline_keyboard: [[{ text: '📱 Get Numbers', callback_data: 'get_numbers' }]] }
    });
  }

  // GET COUNTRIES
  if (data === 'get_numbers') {
    const api = await fetchNumbersAPI();
    const countries = api.countries || [];

    const keyboard = countries.map(c => [
      { text: `${c.flag} ${c.country}`, callback_data: `country_${c.code}` }
    ]);

    bot.editMessageText('🌍 *Select Country*', {
      chat_id: chatId,
      message_id: msgId,
      parse_mode: 'Markdown',
      reply_markup: { inline_keyboard: keyboard }
    });
  }

  // COUNTRY SELECT
  if (data.startsWith('country_')) {
    const code = data.replace('country_', '');
    const api = await fetchNumbersAPI();
    const country = api.countries.find(c => c.code === code);

    if (!country || !country.numbers.length) {
      bot.answerCallbackQuery(q.id, { text: '❌ No numbers', show_alert: true });
      return;
    }

    const number = country.numbers[Math.floor(Math.random() * country.numbers.length)];
    numberUserMap.set(number, userId);

    bot.editMessageText(
      `🌍 *${country.flag} ${country.country}*\n\n📱 Number:\n\`${number}\`\n\n⏳ OTP automatic milega`,
      {
        chat_id: chatId,
        message_id: msgId,
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: [
            [{ text: '💬 OTP Group', url: 'https://t.me/otpgrouptempno' }],
            [{ text: '⏭️ Next', callback_data: `country_${code}` }],
            [{ text: '🔙 Back', callback_data: 'get_numbers' }]
          ]
        }
      }
    );
  }
});

// ================= AUTO OTP FETCH =================
setInterval(async () => {
  try {
    const data = await fetchSMSAPI();
    if (!data.sms) return;

    for (const sms of data.sms) {
      const key = sms.number + sms.message;
      if (seenOtps.has(key)) continue;
      seenOtps.add(key);

      // SEND TO GROUP
      await bot.sendMessage(
        OTP_GROUP_ID,
        `📩 *OTP*\n📞 ${sms.number}\n💬 ${sms.message}`,
        { parse_mode: 'Markdown' }
      );

      // SEND TO USER
      if (numberUserMap.has(sms.number)) {
        const uid = numberUserMap.get(sms.number);
        await bot.sendMessage(
          uid,
          `✅ *Your OTP*\n\n📞 ${sms.number}\n💬 ${sms.message}`,
          { parse_mode: 'Markdown' }
        );
        numberUserMap.delete(sms.number);
      }
    }
  } catch (e) {
    console.log('SMS fetch error');
  }
}, 10000);
