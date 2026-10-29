// Simple back-and-forth motion along X for demo scenes.
// Attach to a character; tune leftX/rightX and timings in the Inspector.
// Update() advances a repeating cycle: move right, pause, move left, pause.

using UnityEngine;

public class CharacterMotion : MonoBehaviour
{
    // Left and right stopping positions.
    [SerializeField] private float leftX = -5f;
    [SerializeField] private float rightX = 5f;

    // Time spent traveling in one direction.
    [SerializeField] private float travelTime = 5f;

    // Time spent stopped at each end.
    [SerializeField] private float stopTime = 1f;

    // Time within the complete out-and-back cycle.
    private double elapsedTime;

    private void Start()
    {
        // Start at the left endpoint.
        transform.position = new Vector3(
            leftX,
            transform.position.y,
            transform.position.z
        );
    }

    private void Update()
    {
        Advance(Time.deltaTime);
    }

    private void Advance(float deltaTime)
    {
        // Prevent invalid duration settings.
        float duration = Mathf.Max(0.01f, travelTime);

        double legTime = (double)duration + Mathf.Max(0f, stopTime);
        // Keep leftover time across every transition, even after a long frame.
        elapsedTime = (elapsedTime + deltaTime) % (2.0 * legTime);
        bool movingRight = elapsedTime < legTime;
        double legElapsed = movingRight ? elapsedTime : elapsedTime - legTime;

        // Calculate how far through the trip we are.
        float progress = Mathf.Clamp01(
            (float)(legElapsed / duration)
        );

        // Smooth acceleration and deceleration.
        // Speed begins at zero, increases,
        // then falls back to zero.
        float smoothProgress = Mathf.SmoothStep(
            0f, 1f, progress
        );

        float startX = movingRight ? leftX : rightX;
        float endX = movingRight ? rightX : leftX;

        // Move along the X axis.
        float x = Mathf.Lerp(
            startX, endX, smoothProgress
        );

        transform.position = new Vector3(
            x,
            transform.position.y,
            transform.position.z
        );

    }
}

