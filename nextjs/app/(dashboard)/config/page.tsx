"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Settings, CheckCircle2, AlertCircle, Eye, EyeOff, Plus, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export default function Configuration() {
  const { toast } = useToast();
  const [showToken, setShowToken] = useState(false);
  const [showSID, setShowSID] = useState(false);
  const [redKeywords, setRedKeywords] = useState([
    "difficulté à respirer",
    "douleur 9/10",
    "température 39.5"
  ]);
  const [orangeKeywords, setOrangeKeywords] = useState([
    "légère nausée",
    "sommeil agité",
    "petite douleur"
  ]);
  const [newRedKeyword, setNewRedKeyword] = useState("");
  const [newOrangeKeyword, setNewOrangeKeyword] = useState("");

  const handleSaveConfig = (tabName: string) => {
    toast({
      title: "Configuration Saved",
      description: `${tabName} settings have been updated successfully.`,
    });
  };

  const handleTestSMS = () => {
    toast({
      title: "Test SMS Sent",
      description: "A test message has been dispatched via Twilio.",
    });
  };

  const addRedKeyword = () => {
    if (newRedKeyword.trim()) {
      setRedKeywords([...redKeywords, newRedKeyword.trim()]);
      setNewRedKeyword("");
    }
  };

  const addOrangeKeyword = () => {
    if (newOrangeKeyword.trim()) {
      setOrangeKeywords([...orangeKeywords, newOrangeKeyword.trim()]);
      setNewOrangeKeyword("");
    }
  };

  const removeRedKeyword = (index: number) => {
    setRedKeywords(redKeywords.filter((_, i) => i !== index));
  };

  const removeOrangeKeyword = (index: number) => {
    setOrangeKeywords(orangeKeywords.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Settings className="h-8 w-8 text-accent" />
        <div>
          <h1 className="text-3xl font-bold">Configuration</h1>
          <p className="text-muted-foreground mt-1">
            System settings and administration
          </p>
        </div>
      </div>

      <Tabs defaultValue="system" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="system">System Status & Keys</TabsTrigger>
          <TabsTrigger value="scheduling">Follow-up & Scheduling</TabsTrigger>
          <TabsTrigger value="alerts">Alert Thresholds</TabsTrigger>
        </TabsList>

        {/* Tab 1: System Status & Keys */}
        <TabsContent value="system" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>ADK Status</CardTitle>
              <CardDescription>Agent Orchestrator connectivity status</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-6 w-6 text-safe" />
                <span className="text-sm font-medium">Agent Orchestrator Online</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Twilio Connection</CardTitle>
              <CardDescription>SMS messaging service configuration</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="twilio-sid">Twilio Account SID</Label>
                <div className="relative">
                  <Input
                    id="twilio-sid"
                    type={showSID ? "text" : "password"}
                    placeholder="AC••••••••••••••••••••••••••••••"
                    defaultValue="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-1/2 -translate-y-1/2"
                    onClick={() => setShowSID(!showSID)}
                  >
                    {showSID ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="twilio-token">Auth Token</Label>
                <div className="relative">
                  <Input
                    id="twilio-token"
                    type={showToken ? "text" : "password"}
                    placeholder="••••••••••••••••••••••••••••••••"
                    defaultValue="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-1/2 -translate-y-1/2"
                    onClick={() => setShowToken(!showToken)}
                  >
                    {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="messaging-service">Messaging Service ID</Label>
                <Input
                  id="messaging-service"
                  placeholder="MGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                  defaultValue="MGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                />
              </div>

              <Button onClick={handleTestSMS} variant="outline">
                Send Test SMS
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>LLM Configuration</CardTitle>
              <CardDescription>AI model used for patient analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between p-3 bg-muted rounded-md">
                <span className="text-sm font-medium">Current Model:</span>
                <span className="text-sm text-muted-foreground">Gemini 2.5 Pro</span>
              </div>
            </CardContent>
          </Card>

          <Button onClick={() => handleSaveConfig("System")} className="w-full">
            Save Configuration
          </Button>
        </TabsContent>

        {/* Tab 2: Follow-up & Scheduling */}
        <TabsContent value="scheduling" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Default Follow-up Duration</CardTitle>
              <CardDescription>Standard patient monitoring period</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="duration">Follow-up Period (days)</Label>
                <Input id="duration" type="number" defaultValue="14" min="1" max="90" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Check-up Frequency Configuration</CardTitle>
              <CardDescription>Automated check-up schedules and templates</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border border-border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Post-Op Check-up</span>
                  <Button variant="ghost" size="sm">Edit Template</Button>
                </div>
                <div className="text-sm text-muted-foreground">
                  <span className="font-medium">Time:</span> J+3 at 10:00 AM
                </div>
              </div>

              <div className="border border-border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Daily Medication Reminder</span>
                  <Button variant="ghost" size="sm">Edit Template</Button>
                </div>
                <div className="text-sm text-muted-foreground">
                  <span className="font-medium">Time:</span> 18:00 PM
                </div>
              </div>

              <div className="border border-border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Weekly Status Check</span>
                  <Button variant="ghost" size="sm">Edit Template</Button>
                </div>
                <div className="text-sm text-muted-foreground">
                  <span className="font-medium">Time:</span> Every Monday at 09:00 AM
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Default Message Template</CardTitle>
              <CardDescription>Generic template for automated messages</CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea
                placeholder="Hello [Patient Name], how are you feeling today?"
                defaultValue="Bonjour [Patient Name], comment vous sentez-vous aujourd'hui ? Merci de répondre avec vos symptômes ou 'Bien' si tout va bien."
                rows={4}
              />
            </CardContent>
          </Card>

          <Button onClick={() => handleSaveConfig("Scheduling")} className="w-full">
            Save Configuration
          </Button>
        </TabsContent>

        {/* Tab 3: Alert Thresholds */}
        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-critical" />
                RED Alert Triggers (Critical)
              </CardTitle>
              <CardDescription>
                Keywords and phrases that require immediate intervention
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Add new trigger..."
                  value={newRedKeyword}
                  onChange={(e) => setNewRedKeyword(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addRedKeyword()}
                />
                <Button onClick={addRedKeyword} size="icon">
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              <div className="space-y-2">
                {redKeywords.map((keyword, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-critical/10 border border-critical/20 rounded-md"
                  >
                    <span className="text-sm">{keyword}</span>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeRedKeyword(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-warning" />
                ORANGE Alert Triggers (Warning)
              </CardTitle>
              <CardDescription>
                Keywords requiring closer monitoring but not immediate dispatch
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Add new trigger..."
                  value={newOrangeKeyword}
                  onChange={(e) => setNewOrangeKeyword(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addOrangeKeyword()}
                />
                <Button onClick={addOrangeKeyword} size="icon">
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              <div className="space-y-2">
                {orangeKeywords.map((keyword, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-warning/10 border border-warning/20 rounded-md"
                  >
                    <span className="text-sm">{keyword}</span>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeOrangeKeyword(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Inactivity Threshold</CardTitle>
              <CardDescription>
                Time before non-response generates an alert
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="inactivity">Hours of Inactivity</Label>
                <Input id="inactivity" type="number" defaultValue="24" min="1" max="72" />
                <p className="text-xs text-muted-foreground">
                  System will generate an ORANGE alert if patient doesn't respond within this timeframe
                </p>
              </div>
            </CardContent>
          </Card>

          <Button onClick={() => handleSaveConfig("Alert Thresholds")} className="w-full">
            Save Configuration
          </Button>
        </TabsContent>
      </Tabs>
    </div>
  );
}
