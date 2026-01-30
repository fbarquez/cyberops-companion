"use client";

import { useQuery } from "@tanstack/react-query";
import { FileText, Copy, Download, Mail, Users, Building } from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { useUIStore } from "@/stores/ui-store";
import { useTranslations } from "@/hooks/use-translations";
import { toolsAPI } from "@/lib/api-client";

export default function TemplatesPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const { language } = useUIStore();

  const { data: templates, isLoading } = useQuery({
    queryKey: ["templates", language],
    queryFn: () => toolsAPI.getTemplates(token!, language),
    enabled: !!token,
  });

  if (isLoading) return <PageLoading />;

  const templateList = (templates as any[]) || [];
  const categories = Array.from(new Set(templateList.map((t) => t.category)));

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "communication":
        return Mail;
      case "reporting":
        return FileText;
      case "compliance":
        return Building;
      default:
        return FileText;
    }
  };

  return (
    <div className="flex flex-col h-full">
      <Header title={t("nav.templates")} />

      <div className="p-6 space-y-6">
        <Tabs defaultValue={categories[0]}>
          <TabsList>
            {categories.map((category) => {
              const Icon = getCategoryIcon(category);
              return (
                <TabsTrigger key={category} value={category} className="capitalize">
                  <Icon className="h-4 w-4 mr-2" />
                  {category}
                </TabsTrigger>
              );
            })}
          </TabsList>

          {categories.map((category) => (
            <TabsContent key={category} value={category} className="mt-4">
              <div className="grid md:grid-cols-2 gap-4">
                {templateList
                  .filter((t) => t.category === category)
                  .map((template: any) => (
                    <TemplateCard key={template.id} template={template} />
                  ))}
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  );
}

function TemplateCard({ template }: { template: any }) {
  const { t } = useTranslations();
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>{template.name}</CardTitle>
            <CardDescription>{template.description}</CardDescription>
          </div>
          <Badge variant="outline" className="capitalize">
            {template.category}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Copy className="h-4 w-4 mr-2" />
            {t("templates.copy")}
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            {t("templates.download")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
