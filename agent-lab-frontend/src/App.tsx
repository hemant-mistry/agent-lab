import Layout from "./Layout"
import Workspace from "./pages/Workspace"

export default function App() {
  return (
    <Layout>
      {/* This renders your new Agent Trace UI inside the main content area */}
      <Workspace />
    </Layout>
  )
}