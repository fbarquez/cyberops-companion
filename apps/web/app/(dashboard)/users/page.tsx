"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Users,
  UserPlus,
  UserX,
  UserCheck,
  Shield,
  Key,
  KeyRound,
  Settings,
  History,
  Mail,
  MoreHorizontal,
  Plus,
  Trash2,
  Edit,
  Eye,
  Clock,
  Monitor,
  Globe,
  Building2,
  UserCog,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { userManagementAPI } from "@/lib/api-client";
import { formatDistanceToNow, format } from "date-fns";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  avatar_url?: string;
  phone?: string;
  timezone?: string;
  language?: string;
  last_login?: string;
  created_at: string;
}

interface Team {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  member_count?: number;
}

interface Role {
  id: string;
  name: string;
  description?: string;
  is_system_role: boolean;
  created_at: string;
  permission_count?: number;
}

interface Permission {
  id: string;
  name: string;
  description?: string;
  resource: string;
  action: string;
}

interface Session {
  id: string;
  user_agent?: string;
  ip_address?: string;
  status: string;
  created_at: string;
  expires_at: string;
  last_activity_at?: string;
}

interface Invitation {
  id: string;
  email: string;
  role: string;
  status: string;
  invited_by?: string;
  expires_at: string;
  created_at: string;
}

interface ActivityLog {
  id: string;
  user_id?: string;
  user_name?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: Record<string, any>;
  ip_address?: string;
  created_at: string;
}

interface APIKey {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  is_active: boolean;
  expires_at?: string;
  last_used_at?: string;
  created_at: string;
}

interface Stats {
  total_users: number;
  active_users: number;
  total_teams: number;
  total_roles: number;
  active_sessions: number;
  pending_invitations: number;
  active_api_keys: number;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export default function UsersPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("users");

  // Dialog states
  const [isTeamDialogOpen, setIsTeamDialogOpen] = useState(false);
  const [isRoleDialogOpen, setIsRoleDialogOpen] = useState(false);
  const [isInvitationDialogOpen, setIsInvitationDialogOpen] = useState(false);
  const [isAPIKeyDialogOpen, setIsAPIKeyDialogOpen] = useState(false);

  // Form states
  const [teamForm, setTeamForm] = useState({ name: "", description: "" });
  const [roleForm, setRoleForm] = useState({ name: "", description: "" });
  const [invitationForm, setInvitationForm] = useState({ email: "", role: "analyst" });
  const [apiKeyForm, setApiKeyForm] = useState({ name: "", scopes: ["read"], expires_in_days: 90 });

  // Stats
  const { data: stats } = useQuery({
    queryKey: ["user-management-stats"],
    queryFn: () => userManagementAPI.getStats(token!) as Promise<Stats>,
    enabled: !!token,
  });

  // Users
  const { data: usersData, isLoading: loadingUsers } = useQuery({
    queryKey: ["users-list"],
    queryFn: () => userManagementAPI.listUsers(token!, { size: 100 }) as Promise<PaginatedResponse<User>>,
    enabled: !!token && activeTab === "users",
  });

  // Teams
  const { data: teamsData, isLoading: loadingTeams } = useQuery({
    queryKey: ["teams-list"],
    queryFn: () => userManagementAPI.listTeams(token!, { size: 100 }) as Promise<PaginatedResponse<Team>>,
    enabled: !!token && activeTab === "teams",
  });

  // Roles
  const { data: rolesData, isLoading: loadingRoles } = useQuery({
    queryKey: ["roles-list"],
    queryFn: () => userManagementAPI.listRoles(token!, { size: 100 }) as Promise<PaginatedResponse<Role>>,
    enabled: !!token && activeTab === "roles",
  });

  // Permissions
  const { data: permissionsData } = useQuery({
    queryKey: ["permissions-list"],
    queryFn: () => userManagementAPI.listPermissions(token!) as Promise<Permission[]>,
    enabled: !!token && activeTab === "roles",
  });

  // Sessions
  const { data: sessionsData, isLoading: loadingSessions } = useQuery({
    queryKey: ["my-sessions"],
    queryFn: () => userManagementAPI.getMySessions(token!) as Promise<Session[]>,
    enabled: !!token && activeTab === "sessions",
  });

  // Invitations
  const { data: invitationsData, isLoading: loadingInvitations } = useQuery({
    queryKey: ["invitations-list"],
    queryFn: () => userManagementAPI.listInvitations(token!, { size: 100 }) as Promise<PaginatedResponse<Invitation>>,
    enabled: !!token && activeTab === "invitations",
  });

  // Activity Logs
  const { data: activityLogsData, isLoading: loadingActivityLogs } = useQuery({
    queryKey: ["activity-logs"],
    queryFn: () => userManagementAPI.listActivityLogs(token!, { size: 100 }) as Promise<PaginatedResponse<ActivityLog>>,
    enabled: !!token && activeTab === "activity",
  });

  // API Keys
  const { data: apiKeysData, isLoading: loadingAPIKeys } = useQuery({
    queryKey: ["api-keys-list"],
    queryFn: () => userManagementAPI.listAPIKeys(token!) as Promise<APIKey[]>,
    enabled: !!token && activeTab === "apikeys",
  });

  // Mutations
  const createTeamMutation = useMutation({
    mutationFn: (data: any) => userManagementAPI.createTeam(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teams-list"] });
      queryClient.invalidateQueries({ queryKey: ["user-management-stats"] });
      setIsTeamDialogOpen(false);
      setTeamForm({ name: "", description: "" });
    },
  });

  const deleteTeamMutation = useMutation({
    mutationFn: (id: string) => userManagementAPI.deleteTeam(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teams-list"] });
      queryClient.invalidateQueries({ queryKey: ["user-management-stats"] });
    },
  });

  const createRoleMutation = useMutation({
    mutationFn: (data: any) => userManagementAPI.createRole(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roles-list"] });
      queryClient.invalidateQueries({ queryKey: ["user-management-stats"] });
      setIsRoleDialogOpen(false);
      setRoleForm({ name: "", description: "" });
    },
  });

  const deleteRoleMutation = useMutation({
    mutationFn: (id: string) => userManagementAPI.deleteRole(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roles-list"] });
      queryClient.invalidateQueries({ queryKey: ["user-management-stats"] });
    },
  });

  const createInvitationMutation = useMutation({
    mutationFn: (data: any) => userManagementAPI.createInvitation(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invitations-list"] });
      queryClient.invalidateQueries({ queryKey: ["user-management-stats"] });
      setIsInvitationDialogOpen(false);
      setInvitationForm({ email: "", role: "analyst" });
    },
  });

  const revokeInvitationMutation = useMutation({
    mutationFn: (id: string) => userManagementAPI.revokeInvitation(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invitations-list"] });
      queryClient.invalidateQueries({ queryKey: ["user-management-stats"] });
    },
  });

  const revokeSessionMutation = useMutation({
    mutationFn: (id: string) => userManagementAPI.revokeSession(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-sessions"] });
      queryClient.invalidateQueries({ queryKey: ["user-management-stats"] });
    },
  });

  const createAPIKeyMutation = useMutation({
    mutationFn: (data: any) => userManagementAPI.createAPIKey(token!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys-list"] });
      queryClient.invalidateQueries({ queryKey: ["user-management-stats"] });
      setIsAPIKeyDialogOpen(false);
      setApiKeyForm({ name: "", scopes: ["read"], expires_in_days: 90 });
    },
  });

  const revokeAPIKeyMutation = useMutation({
    mutationFn: (id: string) => userManagementAPI.revokeAPIKey(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys-list"] });
      queryClient.invalidateQueries({ queryKey: ["user-management-stats"] });
    },
  });

  const deactivateUserMutation = useMutation({
    mutationFn: (id: string) => userManagementAPI.deactivateUser(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users-list"] });
      queryClient.invalidateQueries({ queryKey: ["user-management-stats"] });
    },
  });

  const activateUserMutation = useMutation({
    mutationFn: (id: string) => userManagementAPI.activateUser(token!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users-list"] });
      queryClient.invalidateQueries({ queryKey: ["user-management-stats"] });
    },
  });

  const users = usersData?.items || [];
  const teams = teamsData?.items || [];
  const roles = rolesData?.items || [];
  const permissions = permissionsData || [];
  const sessions = sessionsData || [];
  const invitations = invitationsData?.items || [];
  const activityLogs = activityLogsData?.items || [];
  const apiKeys = apiKeysData || [];

  const getStatusBadge = (isActive: boolean) => {
    return isActive ? (
      <Badge variant="default">{t("users.active")}</Badge>
    ) : (
      <Badge variant="secondary">{t("users.inactive")}</Badge>
    );
  };

  const getInvitationStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      pending: "secondary",
      accepted: "default",
      expired: "outline",
      revoked: "destructive",
    };
    return <Badge variant={variants[status] || "secondary"}>{status}</Badge>;
  };

  const getRoleBadge = (role: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      admin: "destructive",
      manager: "default",
      analyst: "secondary",
      viewer: "outline",
    };
    return <Badge variant={variants[role] || "secondary"}>{role}</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t("users.title")}</h1>
          <p className="text-muted-foreground">
            {t("users.subtitle")}
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">{t("users.totalUsers")}</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_users || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.active_users || 0} {t("users.activeCount")}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">{t("users.totalTeams")}</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_teams || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">{t("users.activeSessions")}</CardTitle>
            <Monitor className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.active_sessions || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">{t("users.pendingInvitations")}</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.pending_invitations || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="users" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            <span className="hidden sm:inline">{t("users.usersList")}</span>
          </TabsTrigger>
          <TabsTrigger value="teams" className="flex items-center gap-2">
            <Building2 className="h-4 w-4" />
            <span className="hidden sm:inline">{t("users.teams")}</span>
          </TabsTrigger>
          <TabsTrigger value="roles" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            <span className="hidden sm:inline">{t("users.roles")}</span>
          </TabsTrigger>
          <TabsTrigger value="sessions" className="flex items-center gap-2">
            <Monitor className="h-4 w-4" />
            <span className="hidden sm:inline">{t("users.sessions")}</span>
          </TabsTrigger>
          <TabsTrigger value="invitations" className="flex items-center gap-2">
            <Mail className="h-4 w-4" />
            <span className="hidden sm:inline">{t("users.invitations")}</span>
          </TabsTrigger>
          <TabsTrigger value="activity" className="flex items-center gap-2">
            <History className="h-4 w-4" />
            <span className="hidden sm:inline">{t("users.activityLog")}</span>
          </TabsTrigger>
          <TabsTrigger value="apikeys" className="flex items-center gap-2">
            <Key className="h-4 w-4" />
            <span className="hidden sm:inline">{t("users.apiKeys")}</span>
          </TabsTrigger>
        </TabsList>

        {/* Users Tab */}
        <TabsContent value="users" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={isInvitationDialogOpen} onOpenChange={setIsInvitationDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <UserPlus className="h-4 w-4 mr-2" />
                  {t("users.inviteUser")}
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{t("users.inviteUser")}</DialogTitle>
                  <DialogDescription>
                    {t("users.invitationDescription")}
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>{t("users.email")}</Label>
                    <Input
                      type="email"
                      value={invitationForm.email}
                      onChange={(e) => setInvitationForm({ ...invitationForm, email: e.target.value })}
                      placeholder="user@example.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t("users.role")}</Label>
                    <Select
                      value={invitationForm.role}
                      onValueChange={(v) => setInvitationForm({ ...invitationForm, role: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="admin">{t("users.roleAdmin")}</SelectItem>
                        <SelectItem value="manager">{t("users.roleManager")}</SelectItem>
                        <SelectItem value="analyst">{t("users.roleAnalyst")}</SelectItem>
                        <SelectItem value="viewer">{t("users.roleViewer")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsInvitationDialogOpen(false)}>
                    {t("users.cancel")}
                  </Button>
                  <Button
                    onClick={() => createInvitationMutation.mutate(invitationForm)}
                    disabled={!invitationForm.email}
                  >
                    {t("users.sendInvitation")}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("users.fullName")}</TableHead>
                  <TableHead>{t("users.email")}</TableHead>
                  <TableHead>{t("users.roleHeader")}</TableHead>
                  <TableHead>{t("users.statusHeader")}</TableHead>
                  <TableHead>{t("users.lastLogin")}</TableHead>
                  <TableHead className="text-right">{t("common.actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loadingUsers ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8">
                      {t("users.loading")}
                    </TableCell>
                  </TableRow>
                ) : users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      {t("users.noUsers")}
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">{user.full_name}</TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>{getRoleBadge(user.role)}</TableCell>
                      <TableCell>{getStatusBadge(user.is_active)}</TableCell>
                      <TableCell>
                        {user.last_login
                          ? formatDistanceToNow(new Date(user.last_login), { addSuffix: true })
                          : t("users.never")}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>
                              <Eye className="h-4 w-4 mr-2" />
                              {t("users.viewDetails")}
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Edit className="h-4 w-4 mr-2" />
                              {t("users.editUser")}
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            {user.is_active ? (
                              <DropdownMenuItem
                                className="text-destructive"
                                onClick={() => deactivateUserMutation.mutate(user.id)}
                              >
                                <UserX className="h-4 w-4 mr-2" />
                                {t("users.deactivate")}
                              </DropdownMenuItem>
                            ) : (
                              <DropdownMenuItem
                                onClick={() => activateUserMutation.mutate(user.id)}
                              >
                                <UserCheck className="h-4 w-4 mr-2" />
                                {t("users.activate")}
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        {/* Teams Tab */}
        <TabsContent value="teams" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={isTeamDialogOpen} onOpenChange={setIsTeamDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  {t("users.createTeam")}
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{t("users.createTeam")}</DialogTitle>
                  <DialogDescription>
                    {t("users.teamDialogDescription")}
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>{t("users.teamName")}</Label>
                    <Input
                      value={teamForm.name}
                      onChange={(e) => setTeamForm({ ...teamForm, name: e.target.value })}
                      placeholder={t("users.teamNamePlaceholder")}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t("users.description")}</Label>
                    <Textarea
                      value={teamForm.description}
                      onChange={(e) => setTeamForm({ ...teamForm, description: e.target.value })}
                      placeholder={t("users.teamDescriptionPlaceholder")}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsTeamDialogOpen(false)}>
                    {t("users.cancel")}
                  </Button>
                  <Button
                    onClick={() => createTeamMutation.mutate(teamForm)}
                    disabled={!teamForm.name}
                  >
                    {t("users.createTeamButton")}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {loadingTeams ? (
              <div className="col-span-full text-center py-8 text-muted-foreground">
                {t("users.loading")}
              </div>
            ) : teams.length === 0 ? (
              <div className="col-span-full">
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <Building2 className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">{t("users.noTeams")}</p>
                  </CardContent>
                </Card>
              </div>
            ) : (
              teams.map((team) => (
                <Card key={team.id}>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">{team.name}</CardTitle>
                        {team.description && (
                          <CardDescription className="mt-1">{team.description}</CardDescription>
                        )}
                      </div>
                      {getStatusBadge(team.is_active)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Users className="h-4 w-4" />
                        {team.member_count || 0} {t("users.members")}
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>
                            <Eye className="h-4 w-4 mr-2" />
                            {t("users.viewMembers")}
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Edit className="h-4 w-4 mr-2" />
                            {t("users.editTeam")}
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => deleteTeamMutation.mutate(team.id)}
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            {t("users.deleteTeam")}
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        {/* Roles Tab */}
        <TabsContent value="roles" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={isRoleDialogOpen} onOpenChange={setIsRoleDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  {t("users.createRole")}
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{t("users.createRole")}</DialogTitle>
                  <DialogDescription>
                    {t("users.roleDialogDescription")}
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>{t("users.roleName")}</Label>
                    <Input
                      value={roleForm.name}
                      onChange={(e) => setRoleForm({ ...roleForm, name: e.target.value })}
                      placeholder={t("users.roleNamePlaceholder")}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t("users.description")}</Label>
                    <Textarea
                      value={roleForm.description}
                      onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })}
                      placeholder={t("users.roleDescriptionPlaceholder")}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsRoleDialogOpen(false)}>
                    {t("users.cancel")}
                  </Button>
                  <Button
                    onClick={() => createRoleMutation.mutate(roleForm)}
                    disabled={!roleForm.name}
                  >
                    {t("users.createRoleButton")}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>{t("users.roles")}</CardTitle>
                <CardDescription>{t("users.manageRolesDescription")}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {loadingRoles ? (
                    <div className="text-center py-4 text-muted-foreground">{t("users.loading")}</div>
                  ) : roles.length === 0 ? (
                    <div className="text-center py-4 text-muted-foreground">{t("users.noRoles")}</div>
                  ) : (
                    roles.map((role) => (
                      <div
                        key={role.id}
                        className="flex items-center justify-between p-3 border rounded-lg"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{role.name}</span>
                            {role.is_system_role && (
                              <Badge variant="outline">{t("users.systemRole")}</Badge>
                            )}
                          </div>
                          {role.description && (
                            <p className="text-sm text-muted-foreground">{role.description}</p>
                          )}
                        </div>
                        {!role.is_system_role && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => deleteRoleMutation.mutate(role.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t("users.permissions")}</CardTitle>
                <CardDescription>{t("users.availablePermissions")}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {permissions.length === 0 ? (
                    <div className="text-center py-4 text-muted-foreground">{t("users.noPermissions")}</div>
                  ) : (
                    permissions.map((permission) => (
                      <div
                        key={permission.id}
                        className="flex items-center justify-between p-2 text-sm border-b last:border-0"
                      >
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{permission.resource}</Badge>
                          <span>{permission.action}</span>
                        </div>
                        <span className="text-muted-foreground text-xs">{permission.name}</span>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Sessions Tab */}
        <TabsContent value="sessions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("users.yourActiveSessions")}</CardTitle>
              <CardDescription>{t("users.manageSessionsDescription")}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {loadingSessions ? (
                  <div className="text-center py-8 text-muted-foreground">{t("users.loading")}</div>
                ) : sessions.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">{t("users.noSessions")}</div>
                ) : (
                  sessions.map((session) => (
                    <div
                      key={session.id}
                      className="flex items-center justify-between p-4 border rounded-lg"
                    >
                      <div className="flex items-center gap-4">
                        <div className="p-2 bg-muted rounded-lg">
                          <Monitor className="h-5 w-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">
                              {session.user_agent || t("users.unknownDevice")}
                            </span>
                            <Badge variant={session.status === "active" ? "default" : "secondary"}>
                              {session.status}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            {session.ip_address && (
                              <span className="flex items-center gap-1">
                                <Globe className="h-3 w-3" />
                                {session.ip_address}
                              </span>
                            )}
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {t("users.lastActive")} {formatDistanceToNow(new Date(session.last_activity_at || session.created_at), { addSuffix: true })}
                            </span>
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => revokeSessionMutation.mutate(session.id)}
                      >
                        {t("users.revokeSession")}
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Invitations Tab */}
        <TabsContent value="invitations" className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setIsInvitationDialogOpen(true)}>
              <Mail className="h-4 w-4 mr-2" />
              {t("users.inviteUser")}
            </Button>
          </div>

          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("users.email")}</TableHead>
                  <TableHead>{t("users.roleHeader")}</TableHead>
                  <TableHead>{t("users.statusHeader")}</TableHead>
                  <TableHead>{t("users.expiresHeader")}</TableHead>
                  <TableHead>{t("users.sentHeader")}</TableHead>
                  <TableHead className="text-right">{t("common.actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loadingInvitations ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8">
                      {t("users.loading")}
                    </TableCell>
                  </TableRow>
                ) : invitations.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      {t("users.noInvitations")}
                    </TableCell>
                  </TableRow>
                ) : (
                  invitations.map((invitation) => (
                    <TableRow key={invitation.id}>
                      <TableCell className="font-medium">{invitation.email}</TableCell>
                      <TableCell>{getRoleBadge(invitation.role)}</TableCell>
                      <TableCell>{getInvitationStatusBadge(invitation.status)}</TableCell>
                      <TableCell>
                        {format(new Date(invitation.expires_at), "MMM d, yyyy")}
                      </TableCell>
                      <TableCell>
                        {formatDistanceToNow(new Date(invitation.created_at), { addSuffix: true })}
                      </TableCell>
                      <TableCell className="text-right">
                        {invitation.status === "pending" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => revokeInvitationMutation.mutate(invitation.id)}
                          >
                            {t("users.revokeInvitation")}
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        {/* Activity Log Tab */}
        <TabsContent value="activity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("users.activityLog")}</CardTitle>
              <CardDescription>{t("users.recentActivityDescription")}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {loadingActivityLogs ? (
                  <div className="text-center py-8 text-muted-foreground">{t("users.loading")}</div>
                ) : activityLogs.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">{t("users.noActivityLogs")}</div>
                ) : (
                  activityLogs.map((log) => (
                    <div
                      key={log.id}
                      className="flex items-start gap-4 p-3 border-b last:border-0"
                    >
                      <div className="p-2 bg-muted rounded-lg">
                        <History className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{log.user_name || t("users.system")}</span>
                          <span className="text-muted-foreground">{log.action}</span>
                          <Badge variant="outline">{log.resource_type}</Badge>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground mt-1">
                          <span>{formatDistanceToNow(new Date(log.created_at), { addSuffix: true })}</span>
                          {log.ip_address && <span>IP: {log.ip_address}</span>}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys Tab */}
        <TabsContent value="apikeys" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={isAPIKeyDialogOpen} onOpenChange={setIsAPIKeyDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <KeyRound className="h-4 w-4 mr-2" />
                  {t("users.createAPIKey")}
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{t("users.createAPIKey")}</DialogTitle>
                  <DialogDescription>
                    {t("users.apiKeyDescription")}
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>{t("users.keyName")}</Label>
                    <Input
                      value={apiKeyForm.name}
                      onChange={(e) => setApiKeyForm({ ...apiKeyForm, name: e.target.value })}
                      placeholder={t("users.apiKeyNamePlaceholder")}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t("users.expirationDays")}</Label>
                    <Select
                      value={String(apiKeyForm.expires_in_days)}
                      onValueChange={(v) => setApiKeyForm({ ...apiKeyForm, expires_in_days: parseInt(v) })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="30">{t("users.days30")}</SelectItem>
                        <SelectItem value="90">{t("users.days90")}</SelectItem>
                        <SelectItem value="180">{t("users.days180")}</SelectItem>
                        <SelectItem value="365">{t("users.year1")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsAPIKeyDialogOpen(false)}>
                    {t("users.cancel")}
                  </Button>
                  <Button
                    onClick={() => createAPIKeyMutation.mutate(apiKeyForm)}
                    disabled={!apiKeyForm.name}
                  >
                    {t("users.createAPIKeyButton")}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("users.keyName")}</TableHead>
                  <TableHead>{t("users.keyPrefix")}</TableHead>
                  <TableHead>{t("users.scopes")}</TableHead>
                  <TableHead>{t("users.statusHeader")}</TableHead>
                  <TableHead>{t("users.lastUsed")}</TableHead>
                  <TableHead>{t("users.expiresAt")}</TableHead>
                  <TableHead className="text-right">{t("common.actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loadingAPIKeys ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      {t("users.loading")}
                    </TableCell>
                  </TableRow>
                ) : apiKeys.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      {t("users.noAPIKeys")}
                    </TableCell>
                  </TableRow>
                ) : (
                  apiKeys.map((apiKey) => (
                    <TableRow key={apiKey.id}>
                      <TableCell className="font-medium">{apiKey.name}</TableCell>
                      <TableCell>
                        <code className="text-sm bg-muted px-2 py-1 rounded">{apiKey.prefix}...</code>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1 flex-wrap">
                          {apiKey.scopes.map((scope) => (
                            <Badge key={scope} variant="outline" className="text-xs">
                              {scope}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(apiKey.is_active)}</TableCell>
                      <TableCell>
                        {apiKey.last_used_at
                          ? formatDistanceToNow(new Date(apiKey.last_used_at), { addSuffix: true })
                          : t("users.never")}
                      </TableCell>
                      <TableCell>
                        {apiKey.expires_at
                          ? format(new Date(apiKey.expires_at), "MMM d, yyyy")
                          : t("users.never")}
                      </TableCell>
                      <TableCell className="text-right">
                        {apiKey.is_active && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => revokeAPIKeyMutation.mutate(apiKey.id)}
                          >
                            {t("users.revokeAPIKey")}
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
