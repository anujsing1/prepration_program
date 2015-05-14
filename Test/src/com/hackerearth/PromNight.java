package com.hackerearth;

import java.util.Arrays;

public class PromNight {

	public static void main(String[] args) {
		int boysCount = 4;
		int girlsCount = 5;
		int[] boysHt = {2,5,6,8,7};
		int[] girlsHt = {3, 8, 5, 1, 7};
		Arrays.sort(boysHt);
		Arrays.sort(girlsHt);
		int j=girlsHt.length-1, i=boysHt.length-1;
		for (; i>=0 ; i--)
		{
			while(j>=0)
			{
				if(boysHt[i] > girlsHt[j])
				{
					j--;
					break;
				}
				j--;
			}
			if(j<0)
			{
				break;
			}
		}
		if(i==0)
			System.out.println("Success");
	}

}
