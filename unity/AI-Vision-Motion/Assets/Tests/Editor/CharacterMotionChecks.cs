using System;
using System.Reflection;
using UnityEngine;

// Run with -batchmode -nographics -executeMethod CharacterMotionChecks.Run -quit.
// No test package is needed; any failed check makes the batch command fail.
public static class CharacterMotionChecks
{
    private const BindingFlags PrivateInstance = BindingFlags.Instance | BindingFlags.NonPublic;

    public static void Run()
    {
        Check(new[] { 5.5f }, 5f);              // Rest at the right endpoint.
        Check(new[] { 6.5f }, 4.72f);           // Carry the extra half-second into the return trip.
        Check(new[] { 12.5f }, -4.72f);         // Cross a complete cycle in one frame.
        Check(new[] { 4f, 1.5f, 1f }, 4.72f);   // Same elapsed time, different frame boundaries.
        Check(new[] { 5.5f }, 4.72f, 0f);       // No extra stopped frame with zero rest time.
        Check(new[] { 1f }, -5f, 0f, 0f);       // Invalid travel duration still yields a finite position.
        Debug.Log("CharacterMotion: all six timing checks passed.");
    }

    private static void Check(float[] deltas, float expectedX, float stop = 1f, float travel = 5f)
    {
        var subject = new GameObject("CharacterMotionCheck");
        try
        {
            subject.transform.position = new Vector3(100f, 2f, 3f);
            var motion = subject.AddComponent<CharacterMotion>();
            typeof(CharacterMotion).GetField("stopTime", PrivateInstance).SetValue(motion, stop);
            typeof(CharacterMotion).GetField("travelTime", PrivateInstance).SetValue(motion, travel);
            typeof(CharacterMotion).GetMethod("Start", PrivateInstance).Invoke(motion, null);
            var advance = typeof(CharacterMotion).GetMethod("Advance", PrivateInstance);
            foreach (float delta in deltas)
                advance.Invoke(motion, new object[] { delta });

            Vector3 position = subject.transform.position;
            if (float.IsNaN(position.x) || float.IsInfinity(position.x)
                || Mathf.Abs(position.x - expectedX) > 0.001f
                || position.y != 2f || position.z != 3f)
                throw new Exception($"Motion timing check failed: {position}, expected x={expectedX}");
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(subject);
        }
    }
}
