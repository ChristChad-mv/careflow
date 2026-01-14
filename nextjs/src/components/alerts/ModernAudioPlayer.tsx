"use client";

import { useState, useRef, useCallback } from "react";
import { Play, Pause, Loader2, Mic } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { cn } from "@/lib/utils";

interface ModernAudioPlayerProps {
    src: string;
    className?: string;
}

export function ModernAudioPlayer({ src, className }: ModernAudioPlayerProps) {
    const audioRef = useRef<HTMLAudioElement>(null);
    const [isLoaded, setIsLoaded] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);
    const [duration, setDuration] = useState(0);
    const [currentTime, setCurrentTime] = useState(0);

    const handleLoadAndPlay = useCallback(async () => {
        const audio = audioRef.current;
        if (!audio) return;

        // If not loaded yet, set the src and wait for it
        if (!isLoaded) {
            setIsLoading(true);
            audio.src = src;
            audio.load();

            // Wait for the audio to be ready
            await new Promise<void>((resolve, reject) => {
                const onCanPlay = () => {
                    audio.removeEventListener('canplaythrough', onCanPlay);
                    audio.removeEventListener('error', onError);
                    resolve();
                };
                const onError = () => {
                    audio.removeEventListener('canplaythrough', onCanPlay);
                    audio.removeEventListener('error', onError);
                    reject(new Error('Failed to load audio'));
                };
                audio.addEventListener('canplaythrough', onCanPlay);
                audio.addEventListener('error', onError);
            });

            setDuration(audio.duration);
            setIsLoaded(true);
            setIsLoading(false);
        }

        // Play the audio
        audio.play();
        setIsPlaying(true);
    }, [src, isLoaded]);

    const togglePlay = () => {
        const audio = audioRef.current;
        if (!audio) return;

        if (!isLoaded) {
            // First click -> load and play
            handleLoadAndPlay();
            return;
        }

        // Already loaded -> just toggle
        if (isPlaying) {
            audio.pause();
            setIsPlaying(false);
        } else {
            audio.play();
            setIsPlaying(true);
        }
    };

    const handleTimeUpdate = () => {
        if (audioRef.current) {
            setCurrentTime(audioRef.current.currentTime);
        }
    };

    const handleEnded = () => {
        setIsPlaying(false);
        setCurrentTime(0);
    };

    const handleSeek = (value: number[]) => {
        if (!audioRef.current || !isLoaded) return;
        audioRef.current.currentTime = value[0];
        setCurrentTime(value[0]);
    };

    const formatTime = (time: number) => {
        if (isNaN(time) || time === 0) return "--:--";
        const minutes = Math.floor(time / 60);
        const seconds = Math.floor(time % 60);
        return `${minutes}:${seconds.toString().padStart(2, "0")}`;
    };

    return (
        <div className={cn("bg-background border rounded-full p-2 flex items-center gap-4 shadow-sm", className)}>
            {/* Audio element - no src until first play */}
            <audio
                ref={audioRef}
                onTimeUpdate={handleTimeUpdate}
                onEnded={handleEnded}
                preload="none"
            />

            <Button
                onClick={togglePlay}
                size="icon"
                className="h-10 w-10 rounded-full shrink-0"
                variant={isPlaying ? "default" : "secondary"}
                disabled={isLoading}
            >
                {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                ) : isPlaying ? (
                    <Pause className="h-4 w-4" />
                ) : (
                    <Play className="h-4 w-4 ml-0.5" />
                )}
            </Button>

            <div className="flex-1 flex flex-col justify-center gap-1.5 min-w-0 pr-4">
                {!isLoaded ? (
                    // "Ready" state - before first play
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Mic className="h-4 w-4" />
                        <span className="font-medium">Recording available</span>
                    </div>
                ) : (
                    // "Loaded" state - show full player
                    <>
                        <Slider
                            value={[currentTime]}
                            max={duration || 100}
                            step={0.1}
                            onValueChange={handleSeek}
                            className="cursor-pointer"
                        />
                        <div className="flex justify-between text-[10px] text-muted-foreground font-medium uppercase tracking-wider">
                            <span>{formatTime(currentTime)}</span>
                            <span>{formatTime(duration)}</span>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
