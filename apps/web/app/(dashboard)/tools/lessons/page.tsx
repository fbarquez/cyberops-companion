"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { GraduationCap, Plus, Search, Tag } from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { toolsAPI } from "@/lib/api-client";

export default function LessonsPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["lessons"],
    queryFn: () => toolsAPI.getLessons(token!),
    enabled: !!token,
  });

  if (isLoading) return <PageLoading />;

  const lessonsData = data as any;
  const lessons = lessonsData?.lessons || [];
  const categories = lessonsData?.categories || [];

  return (
    <div className="flex flex-col h-full">
      <Header title={t("nav.lessons")}>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          {t("lessons.addLesson")}
        </Button>
      </Header>

      <div className="p-6 space-y-6">
        {/* Search and Filters */}
        <div className="flex gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder={t("lessons.searchPlaceholder")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex gap-2">
            {categories.map((category: string) => (
              <Badge
                key={category}
                variant="outline"
                className="cursor-pointer hover:bg-accent capitalize"
              >
                {category}
              </Badge>
            ))}
          </div>
        </div>

        {/* Lessons List */}
        {lessons.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <GraduationCap className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium">{t("lessons.noLessons")}</h3>
              <p className="text-muted-foreground mt-1">
                {t("lessons.emptyDescription")}
              </p>
              <Button className="mt-4">
                <Plus className="h-4 w-4 mr-2" />
                {t("lessons.addFirstLesson")}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {lessons.map((lesson: any) => (
              <LessonCard key={lesson.id} lesson={lesson} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function LessonCard({ lesson }: { lesson: any }) {
  const { t } = useTranslations();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>{lesson.title}</CardTitle>
            <CardDescription>{lesson.description}</CardDescription>
          </div>
          <Badge variant="secondary" className="capitalize">
            {lesson.category}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {lesson.recommendations?.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">{t("lessons.recommendations")}</p>
            <ul className="list-disc list-inside text-sm text-muted-foreground">
              {lesson.recommendations.map((rec: string, idx: number) => (
                <li key={idx}>{rec}</li>
              ))}
            </ul>
          </div>
        )}
        {lesson.tags?.length > 0 && (
          <div className="flex gap-1 mt-4">
            <Tag className="h-4 w-4 text-muted-foreground" />
            {lesson.tags.map((tag: string) => (
              <Badge key={tag} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
