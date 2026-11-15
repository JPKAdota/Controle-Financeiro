import { defineConfig, devices } from '@playwright/test';

/**
 * Consulte https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
    testDir: './e2e',
    /* Execute testes em paralelo para ganhar tempo */
    fullyParallel: true,
    /* Falhe o build na integração contínua (CI) se deixar "test.only" esquecido no meio do código. */
    forbidOnly: !!process.env.CI,
    /* Em CI tenta novamente duas vezes */
    retries: process.env.CI ? 2 : 0,
    /* Opt out in CI */
    workers: process.env.CI ? 1 : undefined,
    /* Relatorios como HTML e saída no terminal */
    reporter: 'html',

    use: {
        /* Define o path base pra o Next.js que foi dev rodando */
        baseURL: 'http://127.0.0.1:3000',
        /* Mostra falhas passo a passo para facilitar no terminal */
        trace: 'on-first-retry',
    },

    /* Configure projetos pros browsers principais. Em dev usaremos o chromium */
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
        // Removi firefox e safira por enquanto pra acelerar os testes nesse boilerplate local de QA
    ],

    /* Inícia o projeto Next.js automaticamente antes da fase de testes começar */
    webServer: {
        command: 'npm run dev',
        url: 'http://127.0.0.1:3000',
        reuseExistingServer: !process.env.CI,
    },
});
