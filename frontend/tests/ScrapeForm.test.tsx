import { render } from '@testing-library/react'
import ScrapeForm from '../components/ScrapeForm'

test('renders form', () => {
  const { getByText } = render(<ScrapeForm />)
  expect(getByText('Start Scraping')).toBeInTheDocument()
})
