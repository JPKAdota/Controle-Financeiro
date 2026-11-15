import '@testing-library/jest-dom'
import { render, screen, waitFor } from '@testing-library/react'
import Page from '../app/page'

// Mock simples caso a página inicial use hooks do Recharts ou roteamento interno
jest.mock('next/navigation', () => ({
    useRouter() {
        return {
            push: jest.fn(),
            replace: jest.fn(),
        };
    },
}));

// Mock do Recharts para evitar bugs no jsdom
jest.mock('recharts', () => ({
    ResponsiveContainer: ({ children }: any) => <div style={{ width: 800, height: 400 }}>{children}</div>,
    AreaChart: ({ children }: any) => <div>{children}</div>,
    Area: () => <div />,
    BarChart: ({ children }: any) => <div>{children}</div>,
    Bar: () => <div />,
    XAxis: () => <div />,
    YAxis: () => <div />,
    CartesianGrid: () => <div />,
    Tooltip: () => <div />,
    Legend: () => <div />,
    Cell: () => <div />,
    PieChart: ({ children }: any) => <div>{children}</div>,
    Pie: () => <div />,
    LineChart: ({ children }: any) => <div>{children}</div>,
    Line: () => <div />,
}));

describe('Página Principal (Dashboard)', () => {
    beforeEach(() => {
        // Adiciona o Mock do fetch Global (o "Mocks" que faltava para a UI renderizar)
        global.fetch = jest.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({
                    metrics: { receitas: 1000, despesas: 400, saldo: 600, investido: 100 },
                    expenses_by_category: [{ name: "Comida", value: 500 }],
                    investments_evolution: [{ data: "Jan", valor: 100 }]
                }),
            })
        ) as jest.Mock;
    });

    afterEach(() => {
        jest.resetAllMocks()
    })

    it('deve renderizar o cabeçalho principal após o carregamento', async () => {
        render(<Page />)

        // Na primeira renderização o state data é null e aparece a mensagem original
        expect(screen.getByText('Carregando gráficos...')).toBeInTheDocument()

        // O WaitFor aguarda o useEffect finalizar a promessa do nosso fetch mockado e re-renderizar
        await waitFor(() => {
            const heading = screen.getByRole('heading', { level: 1 })
            expect(heading).toHaveTextContent('Relatório Financeiro')
        })

        // Valida também se os valores financeiros renderizaram na tela baseados no mock
        expect(screen.getByText('R$ 1.000,00')).toBeInTheDocument()
        expect(screen.getByText('R$ 400,00')).toBeInTheDocument()
        expect(screen.getByText('R$ 600,00')).toBeInTheDocument()
    })
})
