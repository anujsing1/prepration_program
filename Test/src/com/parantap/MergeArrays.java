package com.parantap;

public class MergeArrays {

	public static void main(String[] args) {
		int[] a = { 3, 5, 6, 9, 12, 14, 18, 20, 25, 28 };
		int[] b = { 30, 32, 34, 36, 38, 40, 42, 44, 46, 48 };
		int[] testA = new int[100];
		int[] testB = new int[100];
		
		for(int i=0;i<a.length;i++)
		{
			testA[i]=a[i];
		}
		
		for(int i=0;i<b.length;i++)
		{
			testB[i]=b[i];
		}
		
		mergeArray(testA, testB, b.length);
		for(int i=0;i<2*b.length;i++)
		{
			System.out.println(testB[i]);
		}
	}

	static void mergeArray(int[] a, int[] b, int M) {
		  if(a[0] > b[M-1])
		  {
			  for (int i=M, k=0; k<M;i++,k++)
			  {
				  b[i] = a[k];
			  }
		  }
		  else if (b[0] > a[M-1])
		  {
			  for (int i=0, k=M; i<M; i++,k++)
			  {
				  b[k] = b[i];
				  b[i]=a[i];
			  }
		  }
		  else
		  {
			  for (int i=0;i<2*M;i++)
			  {
				  if(a[i] < b[i])
				  {
					  
				  }
			  }
		  }
	}

}
