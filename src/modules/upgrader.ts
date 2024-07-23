import { MuskEmpireAccount } from '../util/config-schema.js';
import { getUpgrades, Upgrade } from '../api/muskempire/musk-empire-service.js';
import {
    getHeroInfo,
    getProfileInfo,
    improveSkill,
} from '../api/muskempire/musk-empire-api.js';
import { Color, Logger } from '@starkow/logger';
import { isCooldownOver, setCooldown } from './heartbeat.js';
import { formatNumber } from '../util/number.js';

const log = Logger.create('[Upgrader]');

export const upgrader = async (account: MuskEmpireAccount, apiKey: string) => {
    if (!isCooldownOver('noUpgradesUntil', account)) return;

    const upgrades = await getUpgrades(apiKey);
    const {
        data: { data: heroInfo },
    } = await getHeroInfo(apiKey);
    const {
        data: { data: profileInfo },
    } = await getProfileInfo(apiKey);

    const bestUpgrade = upgrades
        .filter((upgrade) => {
            const nextLevel = upgrade.currentLevel + 1;

            const requirement =
                upgrade.levels.find(
                    (requirement) => requirement.level >= nextLevel
                ) || upgrade.levels[upgrade.levels.length - 1];

            try {
                return (
                    upgrade.priceNextLevel <= heroInfo.money &&
                    requirement.requiredHeroLevel <= heroInfo.level &&
                    requirement.requiredFriends <= profileInfo.friends &&
                    Object.entries(requirement.requiredSkills).every(
                        ([skillId, skillLevel]) =>
                            upgrades.find((u) => u.id === skillId)!
                                .currentLevel >= skillLevel
                    )
                );
            } catch (e) {
                console.log(e, upgrade);
                process.exit(1);
            }
        })
        .reduce(
            (best, upgrade) =>
                best === null ||
                upgrade.profitIncrement / upgrade.priceNextLevel >
                    best.profitIncrement / best.priceNextLevel
                    ? upgrade
                    : best,
            null as Upgrade | null
        );

    if (!bestUpgrade) {
        log.info(
            Logger.color(account.clientName, Color.Cyan),
            Logger.color(' | ', Color.Gray),
            `No Upgrades Available`
        );
        setCooldown('noUpgradesUntil', account, 600);
        return;
    }

    heroInfo.money -= bestUpgrade.priceNextLevel;

    await improveSkill(apiKey, bestUpgrade.id);

    log.info(
        Logger.color(account.clientName, Color.Cyan),
        Logger.color(' | ', Color.Gray),
        `Successfully improved`,
        Logger.color(bestUpgrade!.id, Color.Yellow),
        `with price`,
        Logger.color(bestUpgrade!.priceNextLevel.toString(), Color.Magenta),
        `before`,
        Logger.color((bestUpgrade!.currentLevel + 1).toString(), Color.Magenta),
        `Level |\n`,
        `Earnings every hour:`,
        Logger.color(
            formatNumber(bestUpgrade!.profitIncrement + heroInfo.moneyPerHour),
            Color.Magenta
        ),
        Logger.color(`(+${bestUpgrade!.profitIncrement})\n`, Color.Green),
        Logger.color(`Money left:`, Color.Green),
        Logger.color(formatNumber(heroInfo.money), Color.Magenta)
    );

    setCooldown('noUpgradesUntil', account, 10);
};
