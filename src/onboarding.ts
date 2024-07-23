import enquirer from 'enquirer';
import { BaseTelegramClientOptions, TelegramClient } from '@mtcute/node';
import { API_HASH, API_ID } from './env.js';
import { v4 as uuidv4 } from 'uuid';
import { DC_MAPPING_PROD } from '@mtcute/convert';
import { defaultHamsterAccount, Proxy } from './util/config-schema.js';
import { toInputUser } from '@mtcute/node/utils.js';
import { storage } from './index.js';
import { authByTelegramWebApp } from './api/muskempire/musk-empire-api.js';

export async function setupNewAccount(firstTime = false) {
    const { authMethod, clientName } = await enquirer.prompt<{
        authMethod: 'authkey' | 'phone';
        clientName: string;
    }>([
        {
            type: 'input',
            name: 'clientName',
            initial: uuidv4(),
            message: firstTime
                ? '👋 Hi! To get started, you need to add a Telegram account What do you want to call this profile?'
                : '📝 What do you want to call this profile?',
        },
        {
            type: 'select',
            name: 'authMethod',
            message: '🧾 Choose an authorisation method',
            choices: [
                {
                    name: 'phone',
                    message: 'Log in with phone number',
                },
                {
                    name: 'authkey',
                    message: 'Auth Key (HEX)',
                },
            ],
        },
    ]);

    switch (authMethod) {
        case 'authkey':
            await authKeyAuthPrompt(clientName);
            break;
        case 'phone':
            await phoneAuth(clientName);
            break;
        default:
            throw new Error('Unknown auth method');
    }
}

async function phoneAuth(clientName: string) {
    const proxy = await proxyPrompt();

    const tg = new TelegramClient({
        apiId: API_ID,
        apiHash: API_HASH,
        storage: `bot-data/${clientName}`,
    });

    await tg.start({
        phone: async () => {
            const phoneResponse = await enquirer.prompt<{
                phone: string;
            }>({
                type: 'input',
                name: 'phone',
                message: '📞 Enter your phone number',
            });

            return phoneResponse.phone;
        },
        code: async () => {
            const codeResponse = await enquirer.prompt<{
                code: string;
            }>({
                type: 'input',
                name: 'code',
                message: '💬 Enter the code from the SMS',
            });

            return codeResponse.code;
        },
        password: async () => {
            const passwordResponse = await enquirer.prompt<{
                password: string;
            }>({
                type: 'input',
                name: 'password',
                message: '🔑 Enter your password',
            });

            return passwordResponse.password;
        },
    });

    await saveAccount(clientName);
    await tg.close();
}

async function proxyPrompt(): Promise<Proxy | null> {
    const { needProxy } = await enquirer.prompt<{ needProxy: boolean }>({
        type: 'confirm',
        name: 'needProxy',
        message: '🔗 Do I need a proxy to connect?',
    });

    if (!needProxy) return null;

    return enquirer.prompt<Proxy>([
        {
            type: 'input',
            name: 'host',
            message: '🔗 Enter the proxy host',
        },
        {
            type: 'input',
            name: 'port',
            message: '🔗 Enter the proxy port',
        },
        {
            type: 'input',
            name: 'username',
            message: '🔗 Enter the proxy username',
        },
        {
            type: 'input',
            name: 'password',
            message: '🔗 Enter the proxy password',
        },
    ]);
}

export async function authKeyAuthPrompt(clientName: string) {
    const authKeyResponse = await enquirer.prompt<{
        authKey: string;
    }>({
        type: 'input',
        name: 'authKey',
        message: 'Enter of eight (heck)',
    });

    const proxy = await proxyPrompt();

    await authKeyAuth(clientName, authKeyResponse.authKey, '2', true);
}

async function saveAccount(clientName: string) {
    storage.update(async (data) => {
        data.accounts = {
            ...data.accounts,
            [clientName]: {
                ...defaultHamsterAccount,
                clientName,
            },
        };
    });
}

export async function authKeyAuth(
    clientName: string,
    authKey: string,
    dc: string = '1',
    exchangeToHamsterToken: boolean
) {
    const tg = createTelegramClient(clientName);

    await tg.importSession({
        authKey: new Uint8Array(Buffer.from(authKey, 'hex')),
        testMode: false,
        version: 3,
        primaryDcs: DC_MAPPING_PROD[+dc],
    });

    if (exchangeToHamsterToken) {
        await saveAccount(clientName);
    } else {
        await tg.close();
    }
}

export async function getMuskEmpireApiKey(clientName: string) {
    const tg = createTelegramClient(clientName);
    await tg.start();
    const muskEmpirePeer = await tg.resolvePeer('muskempire_bot');
    const muskEmpireUser = toInputUser(muskEmpirePeer);

    const result = await tg.call({
        _: 'messages.requestAppWebView',
        peer: muskEmpirePeer,
        app: {
            _: 'inputBotAppShortName',
            botId: muskEmpireUser,
            shortName: 'game',
        },
        platform: 'android',
    });

    let initDataRaw = result.url
        .split('tgWebAppData=')[1]
        .split('&tgWebAppVersion')[0];

    console.log(result.url);

    initDataRaw = decodeURIComponent(initDataRaw);

    await authByTelegramWebApp(
        {
            data: {
                initData: initDataRaw,
                platform: 'android',
                chatId: '',
                chatType: 'sender',
                chatInstance: '-8493099482055851733',
            },
        },
        null
    );

    await tg.close();
    return {
        initData: initDataRaw,
        apiKey: initDataRaw.split('hash=')[1].split('&')[0],
    };
}

export function createTelegramClient(clientName: string) {
    let opts: BaseTelegramClientOptions = {
        apiId: API_ID,
        apiHash: API_HASH,
        logLevel: 0,
        storage: `bot-data/${clientName}`,
    };

    return new TelegramClient(opts);
}
