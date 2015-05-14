/**
 * 
 */
package com.crest;

import java.util.ArrayList;
import java.util.Scanner;

/**
 * @author govind.gupta
 *
 */
public class ArrayImplementation {
	
	public static boolean quit = false;
	private static int cWidth;
	private static int cHeight;
	private static int[][] shapeArray = null;;

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		int x1=0, y1=0, x2=0, y2=0;
		Character cmd = null;

        do
        {
        	System.out.println("Please enter a command: ");
   	     
            Scanner inputCmd = new Scanner(System.in);
           
            String command = inputCmd.nextLine();
            String[] inputs = command.split(" ");
            System.out.println("Command Entered " + command);
            if (inputs.length >= 1)
            {
            	cmd = inputs[0].charAt(0);
            }
        	if (inputs.length >= 3)
        	{
	        	x1 = Integer.parseInt(inputs[1]);
	        	y1 = Integer.parseInt(inputs[2]);
        	}
        	if (inputs.length == 5)
        	{
	        	x2 = Integer.parseInt(inputs[3]);
	        	y2 = Integer.parseInt(inputs[4]);
        	}
        	drawShape(cmd, x1, y1, x2, y2);
        }while(!quit);
	}

	private static void drawShape(Character cmd, int x1, int y1, int x2, int y2) {
		// TODO Auto-generated method stub
		if ('Q' == Character.toUpperCase(cmd))
		{
			quit = true;
			System.out.println("System Exit!");
		}
		else
		{
			if('C' == Character.toUpperCase(cmd))
			{
				cWidth = x1;
				cHeight = y1;
				shapeArray = new int[cWidth][cHeight];
//				createCanvasString();
				System.out.println();
			}
			else if ('L' == Character.toUpperCase(cmd) || 'R' == Character.toUpperCase(cmd))
			{
				/*shape = new Shape(Character.toUpperCase(cmd), x1, y1, x2, y2);
				shapes.add(shape);
				createCanvasString();*/
				if(null !=  shapeArray)
				{
					if('L' == Character.toUpperCase(cmd))
					{
						if(y1==y2)
						{
							for(int i=x1-1; i<x2;i++)
							{
								shapeArray[i][y1] = 1;
							}
						}
						else if(x1==x2)
						{
							for(int i=y1-1; i<y2;i++)
							{
								shapeArray[i][x1] = 1;
							}
						}
					}
					else if('R' == Character.toUpperCase(cmd))
					{
						for(int i=x1-1; i<x2;i++)
						{
							shapeArray[i][y1] = 1;
							shapeArray[i][y2] = 1;
						}
						for(int i=y1-1; i<y2;i++)
						{
							shapeArray[i][x1] = 1;
							shapeArray[i][x2] = 1;
						}
					}
				}
				for(int[] row : shapeArray) {
		            printRow(row);
		        }
//				System.out.println(shapeArray);
			}
		}
		
		
	}
	
    public static void printRow(int[] row) {
        for (int i : row) {
            System.out.print(i);
            System.out.print("\t");
        }
        System.out.println();
    }
}
