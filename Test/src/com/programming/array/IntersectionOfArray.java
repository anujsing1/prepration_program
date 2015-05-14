/**
 * 
 */
package com.programming.array;

import java.util.HashSet;

/**
 * @author govind.gupta
 *
 */
public class IntersectionOfArray {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		int[] a = new int[] {-2, 1, -3, 4, -1, 2, -5, 6};
		int[] b = new int[] {-2, -1, -3, -4, -5, 1};
		int[] intersect = intersection(a, b);
		for(int i=0; i< intersect.length; i++)
		{
			System.out.println(intersect[i]);
		}
	}

	static int[] intersection(int[] a, int[] b)
	{
		int size = (a.length > b.length? b.length:a.length);
		int[] intersection = new int[size];
		
		HashSet<Integer> set = new HashSet<Integer>();
		int k=0;
		for(int i=0,j=0; i<a.length || j<b.length; )
		{
			if(a.length > i)
			{
				if (!set.add(a[i]))
				{
					intersection[k] = a[i];
					k++;
				}
				i++;
			}
			if(b.length > j)
			{
				if (!set.add(b[j]))
				{
					intersection[k] = b[j];
					k++;
				}
				j++;
			}
		}
		return intersection;
	}
}
