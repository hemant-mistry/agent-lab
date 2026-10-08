import Layout from "./Layout"

export default function App() {
  return (
    <Layout>
      <section className="space-y-2">
        <h1 className="text-2xl font-semibold">Overview</h1>
        <p className="text-muted-foreground">
          Manage your agents and monitor their runs.
        </p>
      </section>
    </Layout>
  )
}