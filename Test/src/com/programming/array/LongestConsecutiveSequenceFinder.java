package com.programming.array;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

public class LongestConsecutiveSequenceFinder {
    public static void main(String[] arg) {
        int[] nums = { 100, 3, 200, 1, 2, 4 };
        nums = new int[] {-2, 1, -3, 4, -1, 2, 1, -5, 6};
        int[] longestConsecutiveSequence = findLongestConsecutiveSequence(nums);

        System.out.println("The longest consecutive sequence is:");
        System.out.println(Arrays.toString(longestConsecutiveSequence));
    }

    public static int[] findLongestConsecutiveSequence(int[] nums) {
        if (nums == null) {
            return new int[0];
        }

        Map<Integer, Integer> numConsecutiveValuesStartingFrom = new HashMap<Integer, Integer>();

        for (int num : nums) {
            numConsecutiveValuesStartingFrom.put(num, 0);
        }

        int n = nums.length;
        int maxNumConsecutiveValues = 0;
        int maxStartIndex = 0;

        for (int i = 0; i < n; ++i) {
            int num = nums[i];
            int numConsecutiveValues = findNumConsecutiveValuesStartingAt(num, numConsecutiveValuesStartingFrom);

            if (numConsecutiveValues > maxNumConsecutiveValues) {
                maxNumConsecutiveValues = numConsecutiveValues;
                maxStartIndex = i;
            }
        }

        int[] longestConsecutiveSequence = new int[maxNumConsecutiveValues];

        for (int i = 0; i < maxNumConsecutiveValues; ++i) {
            int num = nums[maxStartIndex] + i;
            longestConsecutiveSequence[i] = num;
        }

        return longestConsecutiveSequence;
    }

    private static int findNumConsecutiveValuesStartingAt(int num, Map<Integer, Integer> numConsecutiveValuesStartingFrom) {
        boolean isNumInArray = numConsecutiveValuesStartingFrom.containsKey(num);

        if (!isNumInArray) {
            return 0;
        }

        int numConsecutiveValuesStartingFromNum = numConsecutiveValuesStartingFrom.get(num);
        boolean numConsecutiveValuesHaveBeenComputed = (numConsecutiveValuesStartingFromNum != 0);

        if (numConsecutiveValuesHaveBeenComputed) {
            return numConsecutiveValuesStartingFromNum;
        }

        return 1 + findNumConsecutiveValuesStartingAt(num + 1, numConsecutiveValuesStartingFrom);
    }
}
