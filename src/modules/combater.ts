import { MuskEmpireAccount } from '../util/config-schema.js';
import { Color, Logger } from '@starkow/logger';
import {
    claimPvp,
    fightPvp,
    getHeroInfo,
} from '../api/muskempire/musk-empire-api.js';
import { isCooldownOver, setCooldown } from './heartbeat.js';

const log = Logger.create('[Combater]');

let loseStreak = 0;
const strategies = ['flexible', 'aggressive', 'protective'];

let strategy = strategies[1];

let wins = 0;
let losses = 0;
let income = 0;

export const combater = async (account: MuskEmpireAccount, apiKey: string) => {
    if (!isCooldownOver('noPvpUntil', account)) return;

    const {
        data: {
            data: { money },
        },
    } = await getHeroInfo(apiKey);

    if (money < 25000) {
        setCooldown('noPvpUntil', account, 30);
        return;
    }

    const {
        data: {
            data: { opponent, fight, hero },
        },
    } = await fightPvp(apiKey, 'bronze', strategy);

    if (!opponent) return;

    const result = fight.winner === hero.id;

    if (!result) {
        income -= fight.moneyContract;

        losses++;
        loseStreak++;

        if (loseStreak >= 4) {
            await claimPvp(apiKey);
            strategy =
                strategies[Math.floor(Math.random() * strategies.length)];

            loseStreak = 0;
            log.info(
                Logger.color(account.clientName, Color.Cyan),
                Logger.color('|', Color.Gray),
                `A husk streak has been detected`,
                `|`,
                `Sleep for 30 seconds`,
                `|`,
                'The following strategy has been chosen:',
                Logger.color(strategy, Color.Yellow)
            );
            setCooldown('noPvpUntil', account, 30);
            return;
        }
    } else {
        income += fight.moneyProfit;
        wins++;
        loseStreak = 0;
    }
    await claimPvp(apiKey);

    log.info(
        Logger.color(account.clientName, Color.Cyan),
        Logger.color('|', Color.Gray),
        `An attack on`,
        Logger.color(opponent.name, Color.Magenta),
        `|`,
        `Enemy strategy:`,
        Logger.color(fight.player1Strategy, Color.Yellow),
        `|`,
        `Hero strategy:`,
        Logger.color(strategy, Color.Yellow),
        `|`,
        'Income:',
        income > 0
            ? Logger.color(`+${income} 🪙`, Color.Green)
            : Logger.color(`${income} 🪙`, Color.Red),
        `|`,
        'Result:',
        result
            ? Logger.color('Victory', Color.Green)
            : Logger.color('Defeat', Color.Red),
        `|`,
        `Процент побед:`,
        Logger.color(
            ((wins / (wins + losses)) * 100).toFixed(2) + '%',
            Color.Yellow
        )
    );
};
