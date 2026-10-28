
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

    // Progress through the current movement.
    private float elapsedTime = 0f;

    // True: left to right.
    // False: right to left.
    private bool movingRight = true;

    // True while resting at an endpoint.
    private bool stopped = false;

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
        // Prevent invalid duration settings.
        float duration = Mathf.Max(0.01f, travelTime);

        elapsedTime += Time.deltaTime;

        if (stopped)
        {
            // Remain stopped for the specified time.
            if (elapsedTime >= Mathf.Max(0f, stopTime))
            {
                elapsedTime = 0f;
                stopped = false;
                movingRight = !movingRight;
            }

            return;
        }

        // Calculate how far through the trip we are.
        float progress = Mathf.Clamp01(
            elapsedTime / duration
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

        // Finish the trip at the endpoint.
        if (progress >= 1f)
        {
            stopped = true;
            elapsedTime = 0f;
        }
    }
}

