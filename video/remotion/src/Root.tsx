import React from "react";
import { Composition } from "remotion";
import { SettledVideo, totalFrames } from "./SettledVideo";
import { Architecture } from "./Architecture";

const FPS = 30;

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Settled"
      component={SettledVideo}
      durationInFrames={totalFrames(FPS)}
      fps={FPS}
      width={1920}
      height={1080}
    />
    <Composition
      id="Architecture"
      component={Architecture}
      durationInFrames={1}
      fps={FPS}
      width={2400}
      height={1400}
    />
  </>
);
