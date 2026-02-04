export function Table({ children }: { children: React.ReactNode }) {
  return (
    <table className="w-full border-2 border-black border-collapse">
      {children}
    </table>
  )
}

export function TableHeader({ children }: { children: React.ReactNode }) {
  return (
    <thead className="border-b-2 border-black bg-accent-yellow">
      {children}
    </thead>
  )
}

export function TableBody({ children }: { children: React.ReactNode }) {
  return (
    <tbody>
      {children}
    </tbody>
  )
}

export function TableRow({ children }: { children: React.ReactNode }) {
  return (
    <tr className="border-b border-black">
      {children}
    </tr>
  )
}

export function TableCell({ children }: { children: React.ReactNode }) {
  return (
    <td className="px-4 py-3 text-sm">
      {children}
    </td>
  )
}

export function TableHeaderCell({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-3 text-left text-sm font-semibold font-heading">
      {children}
    </th>
  )
}
