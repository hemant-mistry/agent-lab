import { createElement } from "react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

const navigation = [
  { title: "Overview", url: "/" },
  { title: "Agents", url: "/agents" },
  { title: "Runs", url: "/runs" },
  { title: "Settings", url: "/settings" },
]

export function AppSidebar() {
  return (
    <Sidebar variant="inset">
      <SidebarHeader>
        <div className="px-2 py-3">
          <p className="text-lg font-semibold">Agent Lab</p>
          <p className="text-xs text-muted-foreground">
            Agent workspace
          </p>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Workspace</SidebarGroupLabel>

          <SidebarGroupContent>
            <SidebarMenu>
              {navigation.map((item) => (
                <SidebarMenuItem key={item.url}>
                  <SidebarMenuButton
                    render={createElement("a", {
                      href: item.url,
                    })}
                  >
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <p className="px-2 py-2 text-xs text-muted-foreground">
          Agent Lab workspace
        </p>
      </SidebarFooter>
    </Sidebar>
  )
}